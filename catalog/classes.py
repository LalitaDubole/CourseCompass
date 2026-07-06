"""
U3 - OOP / Regex / Threading:
User, Course, Recommender classes with regex validation and
threaded (parallel) catalog searching.
"""
import re
import threading

from catalog.core_logic import compute_skill_gap, rank_course_ids_by_gap_coverage
from catalog.exceptions import UnknownCareerGoalError, InvalidSkillInputError
from catalog.core_logic import CAREER_GOAL_SKILLS


# ---------------- Regex patterns ----------------
SKILL_NAME_PATTERN = re.compile(r"[^a-z0-9\s\+\#\.]")  # strips odd symbols, keeps c++, c#, etc.
COURSE_NAME_PATTERN = re.compile(r"\s+")                # collapses extra whitespace in course titles
EMAIL_PATTERN = re.compile(r"^[\w\.\-]+@[\w\-]+\.[a-zA-Z]{2,}$")


class Skill:
    """Wraps a single skill string and knows how to normalize itself via regex."""

    def __init__(self, raw_name):
        self.raw_name = raw_name
        self.normalized = self._normalize(raw_name)

    @staticmethod
    def _normalize(name):
        name = name.strip().lower()
        name = SKILL_NAME_PATTERN.sub("", name)   # regex: remove stray punctuation
        name = re.sub(r"\s+", " ", name)          # regex: collapse multiple spaces
        return name.strip()

    def __repr__(self):
        return f"Skill('{self.normalized}')"


def normalize_course_name(raw_name):
    """U3 regex: trim + collapse internal whitespace + title-case a course name,
    so 'python   for EVERYBODY' -> 'Python For Everybody'."""
    cleaned = COURSE_NAME_PATTERN.sub(" ", raw_name.strip())
    return cleaned.title()


class User:
    """Represents a learner using CourseCompass."""

    def __init__(self, name, email, career_goal, current_skills):
        if not EMAIL_PATTERN.match(email):
            raise ValueError(f"Invalid email format: {email}")
        if not current_skills:
            raise InvalidSkillInputError("Please enter at least one current skill.")

        self.name = name
        self.email = email
        self.career_goal = career_goal
        self.current_skills = [Skill(s).normalized for s in current_skills]

    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "career_goal": self.career_goal,
            "current_skills": self.current_skills,
        }


class Course:
    """Represents a single course document (mirrors the MongoDB schema)."""

    def __init__(self, name, category, skills_taught, rating=0.0, duration_weeks=4,
                 platform="Self-paced", course_id=None):
        self.course_id = course_id
        self.name = normalize_course_name(name)          # regex-normalized title
        self.category = category
        self.skills_taught = [Skill(s).normalized for s in skills_taught]
        self.rating = float(rating)
        self.duration_weeks = int(duration_weeks)
        self.platform = platform

    @classmethod
    def from_dict(cls, doc):
        return cls(
            name=doc.get("name"),
            category=doc.get("category"),
            skills_taught=doc.get("skills_taught", []),
            rating=doc.get("rating", 0.0),
            duration_weeks=doc.get("duration_weeks", 4),
            platform=doc.get("platform", "Self-paced"),
            course_id=str(doc.get("_id")) if doc.get("_id") else None,
        )

    def to_dict(self):
        return {
            "name": self.name,
            "category": self.category,
            "skills_taught": self.skills_taught,
            "rating": self.rating,
            "duration_weeks": self.duration_weeks,
            "platform": self.platform,
        }

    def __repr__(self):
        return f"Course('{self.name}', rating={self.rating})"


class Recommender:
    """Computes the skill gap for a user and searches the course catalog
    (in parallel, using threading) for the best-matching courses."""

    def __init__(self, user: User, all_courses_raw):
        self.user = user
        # Raw MongoDB documents -> Course objects
        self.all_courses = [Course.from_dict(doc) for doc in all_courses_raw]
        self._lock = threading.Lock()
        self._results = []

    def _required_skills(self):
        if self.user.career_goal not in CAREER_GOAL_SKILLS:
            raise UnknownCareerGoalError(self.user.career_goal)
        return CAREER_GOAL_SKILLS[self.user.career_goal]

    def _search_chunk(self, chunk, gap_skills):
        """Worker function run inside a thread: score each course in this chunk."""
        local_matches = []
        for course in chunk:
            overlap = set(course.skills_taught) & gap_skills
            if overlap:
                local_matches.append((course, len(overlap)))
        with self._lock:
            self._results.extend(local_matches)

    def recommend(self, num_threads=4):
        """U3 threading: split the catalog into chunks and search them
        in parallel threads, then merge + rank results (U1/U2 logic)."""
        required = self._required_skills()
        gap_skills = compute_skill_gap(self.user.current_skills, required)

        if not gap_skills:
            return [], gap_skills  # user already has every required skill

        self._results = []
        chunk_size = max(1, len(self.all_courses) // num_threads)
        chunks = [
            self.all_courses[i:i + chunk_size]
            for i in range(0, len(self.all_courses), chunk_size)
        ]

        threads = []
        for chunk in chunks:
            t = threading.Thread(target=self._search_chunk, args=(chunk, gap_skills))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()  # wait for all threads to finish before ranking

        # lambda-based sort: highest gap-coverage first, then highest rating
        ranked = sorted(
            self._results,
            key=lambda pair: (pair[1], pair[0].rating),
            reverse=True,
        )
        return ranked, gap_skills