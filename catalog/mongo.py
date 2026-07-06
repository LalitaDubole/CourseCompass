"""
U4 - MongoDB: connection handling + CRUD operations for
Courses, User profiles, Bookmarks, and Learning History.
"""
from django.conf import settings
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import certifi
from datetime import datetime, timezone


class MongoConnection:
    """Singleton-style MongoDB connection manager."""
    _client = None
    _db = None

    @classmethod
    def get_db(cls):
        if cls._client is None:
            cls._client = MongoClient(settings.MONGO_URI, tlsCAFile=certifi.where())
            cls._db = cls._client[settings.MONGO_DB_NAME]
        return cls._db


def get_courses_collection():
    db = MongoConnection.get_db()
    return db["courses"]


def get_users_collection():
    db = MongoConnection.get_db()
    return db["users"]


def get_bookmarks_collection():
    db = MongoConnection.get_db()
    return db["bookmarks"]


def get_ratings_collection():
    db = MongoConnection.get_db()
    return db["ratings"]


# ---------------- Course CRUD ----------------

def create_course(course_dict):
    try:
        result = get_courses_collection().insert_one(course_dict)
        return str(result.inserted_id)
    except PyMongoError as e:
        raise RuntimeError(f"Failed to insert course: {e}")


def get_all_courses():
    return list(get_courses_collection().find())


def get_course_by_id(course_id):
    """Fetch a single course document by its MongoDB _id (used to pre-fill the edit form)."""
    from bson import ObjectId
    try:
        return get_courses_collection().find_one({"_id": ObjectId(course_id)})
    except Exception:
        return None


def get_courses_by_skill(skill_name):
    """Query courses whose 'skills_taught' list contains the given skill."""
    return list(get_courses_collection().find({"skills_taught": skill_name}))


def update_course(course_id, updates):
    from bson import ObjectId
    return get_courses_collection().update_one(
        {"_id": ObjectId(course_id)}, {"$set": updates}
    )


def delete_course(course_id):
    from bson import ObjectId
    return get_courses_collection().delete_one({"_id": ObjectId(course_id)})


def update_course_average_rating(course_id):
    """Recompute and store a course's average rating from the ratings collection."""
    from bson import ObjectId
    ratings = list(get_ratings_collection().find({"course_id": course_id}))
    if ratings:
        avg = sum(r["stars"] for r in ratings) / len(ratings)
        get_courses_collection().update_one(
            {"_id": ObjectId(course_id)}, {"$set": {"rating": round(avg, 1)}}
        )


# ---------------- User CRUD ----------------

def create_or_update_user(user_dict):
    """Upsert a user profile by email."""
    return get_users_collection().update_one(
        {"email": user_dict["email"]},
        {"$set": user_dict},
        upsert=True,
    )


def get_user_by_email(email):
    return get_users_collection().find_one({"email": email})


# ---------------- Learning History (U5/U4) ----------------

def add_learning_history_entry(username, career_goal, gap_skills, recommended_course_names):
    """Append one search/recommendation event to this user's learning history."""
    entry = {
        "career_goal": career_goal,
        "gap_skills": gap_skills,
        "recommended_courses": recommended_course_names,
        "viewed_at": datetime.now(timezone.utc).isoformat(),
    }
    get_users_collection().update_one(
        {"username": username},
        {"$push": {"learning_history": entry}},
        upsert=True,
    )


def get_learning_history(username):
    doc = get_users_collection().find_one({"username": username})
    if not doc:
        return []
    return list(reversed(doc.get("learning_history", [])))  # most recent first


# ---------------- Bookmarks ----------------

def add_bookmark(username, course_id, course_name):
    return get_bookmarks_collection().update_one(
        {"username": username, "course_id": course_id},
        {"$set": {"username": username, "course_id": course_id, "course_name": course_name}},
        upsert=True,
    )


def remove_bookmark(username, course_id):
    return get_bookmarks_collection().delete_one({"username": username, "course_id": course_id})


def get_bookmarks_for_user(username):
    return list(get_bookmarks_collection().find({"username": username}))


def is_bookmarked(username, course_id):
    return get_bookmarks_collection().find_one({"username": username, "course_id": course_id}) is not None


# ---------------- Ratings ----------------

def rate_course(username, course_id, stars):
    """Upsert this user's rating (1-5 stars) for a course, then refresh the course's average."""
    get_ratings_collection().update_one(
        {"username": username, "course_id": course_id},
        {"$set": {"username": username, "course_id": course_id, "stars": stars}},
        upsert=True,
    )
    update_course_average_rating(course_id)


def get_user_rating(username, course_id):
    doc = get_ratings_collection().find_one({"username": username, "course_id": course_id})
    return doc["stars"] if doc else None