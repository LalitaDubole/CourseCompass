"""
U1 - Fundamentals: dicts, sets, list comprehensions, conditionals.
This module holds the "plain Python" logic before OOP/threading is layered on.
"""

# Dict: career goal -> set of required skills (skill catalog / mapping)
CAREER_GOAL_SKILLS = {
    "Data Scientist": {"python", "statistics", "machine learning", "sql", "pandas"},
    "Web Developer": {"html", "css", "javascript", "django", "sql"},
    "Data Analyst": {"excel", "sql", "python", "statistics", "power bi"},
    "Android Developer": {"java", "kotlin", "android sdk", "sql", "xml"},
    "Cybersecurity Analyst": {"networking", "linux", "python", "cryptography", "sql"},
    "Cloud Engineer": {"aws", "linux", "docker", "python", "networking"},
    "AI/ML Engineer": {"python", "machine learning", "deep learning", "statistics", "tensorflow"},
}


def get_supported_goals():
    """Return list of career goal names we can recommend for (U1: dict keys)."""
    return list(CAREER_GOAL_SKILLS.keys())


def normalize_skill_list(raw_skills):
    """Convert a comma separated skill string into a clean, lowercase list.
    Uses list comprehension + string methods (U1 fundamentals)."""
    if not raw_skills:
        return []
    return [skill.strip().lower() for skill in raw_skills.split(",") if skill.strip()]


def compute_skill_gap(current_skills, required_skills):
    """Set difference: required - current = the skills the user is missing.
    (U1: sets)"""
    current_set = set(current_skills)
    required_set = set(required_skills)
    gap = required_set - current_set
    return gap


def compute_skill_match_percentage(current_skills, required_skills):
    """What % of the required skills does the user already have (U1: conditionals)."""
    required_set = set(required_skills)
    if not required_set:
        return 0.0
    current_set = set(current_skills)
    matched = required_set & current_set
    return round((len(matched) / len(required_set)) * 100, 1)


def rank_course_ids_by_gap_coverage(courses, gap_skills):
    """For each course, count how many of the gap skills it covers.
    Returns list of (course, coverage_count) sorted high to low.
    Uses list comprehension (U1)."""
    scored = [
        (course, len(set(course.get("skills_taught", [])) & gap_skills))
        for course in courses
    ]
    scored = [pair for pair in scored if pair[1] > 0]  # keep only relevant courses
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored