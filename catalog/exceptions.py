"""
U2 - Functions & Modules: custom exception classes used across the project.
"""


class UnknownCareerGoalError(Exception):
    """Raised when the user selects/enters a career goal we don't have
    a skill-mapping for."""

    def __init__(self, goal_name):
        self.goal_name = goal_name
        super().__init__(
            f"Unknown career goal: '{goal_name}'. "
            f"Please choose a supported goal."
        )


class InvalidSkillInputError(Exception):
    """Raised when the current-skills input is empty or malformed."""

    def __init__(self, message="Skill input is empty or invalid."):
        self.message = message
        super().__init__(self.message)


class CourseNotFoundError(Exception):
    """Raised when a requested course id does not exist in MongoDB."""

    def __init__(self, course_id):
        self.course_id = course_id
        super().__init__(f"Course with id '{course_id}' not found.")