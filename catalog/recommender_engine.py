"""
U2 - Functions & Modules: a function-based wrapper module that ties together
core_logic (U1), classes.py (U3/OOP+threading), and mongo.py (U4)
into one simple call the Django views can use.
"""
from catalog.classes import User, Recommender
from catalog.exceptions import UnknownCareerGoalError, InvalidSkillInputError
from catalog.mongo import get_all_courses, create_or_update_user


def recommend_courses_for_user(name, email, career_goal, raw_current_skills):
    """
    Main entry point used by the Django view.

    Parameters
    ----------
    name : str
    email : str
    career_goal : str
    raw_current_skills : list[str]   e.g. ["python", "sql"]

    Returns
    -------
    dict with keys: gap_skills, recommendations, match_percentage

    Raises
    ------
    UnknownCareerGoalError, InvalidSkillInputError, ValueError
    """
    if not raw_current_skills:
        raise InvalidSkillInputError()

    # 1. Build the User object (U3 OOP) - validates email + normalizes skills
    user = User(
        name=name,
        email=email,
        career_goal=career_goal,
        current_skills=raw_current_skills,
    )

    # 2. Persist/update this user's profile in MongoDB (U4)
    create_or_update_user(user.to_dict())

    # 3. Pull the full course catalog from MongoDB (U4)
    all_courses_raw = get_all_courses()

    # 4. Run the threaded recommender (U3)
    recommender = Recommender(user, all_courses_raw)
    ranked_results, gap_skills = recommender.recommend(num_threads=4)

    # 5. Shape the response using a lambda for final display sorting (U2)
    recommendations = [
        {
            "name": course.name,
            "category": course.category,
            "rating": course.rating,
            "duration_weeks": course.duration_weeks,
            "skills_taught": course.skills_taught,
            "gap_skills_covered": coverage,
        }
        for course, coverage in sorted(
            ranked_results, key=lambda pair: pair[0].rating, reverse=True
        )
    ]

    return {
        "gap_skills": sorted(gap_skills),
        "recommendations": recommendations,
        "career_goal": career_goal,
    }