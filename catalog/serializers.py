"""
U5 - Django REST Framework serializers used by the API endpoints.
"""
from rest_framework import serializers
from catalog.core_logic import get_supported_goals


class RecommendationRequestSerializer(serializers.Serializer):
    """Validates incoming POST data for the /api/recommend/ endpoint."""
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    career_goal = serializers.CharField(max_length=100)
    current_skills = serializers.CharField(
        help_text="Comma-separated skills, e.g. 'python, sql'"
    )

    def validate_career_goal(self, value):
        if value not in get_supported_goals():
            raise serializers.ValidationError(
                f"'{value}' is not a supported career goal. "
                f"Choose from: {', '.join(get_supported_goals())}"
            )
        return value


class CourseOutputSerializer(serializers.Serializer):
    """Shapes a single recommended course for the JSON response."""
    name = serializers.CharField()
    category = serializers.CharField()
    rating = serializers.FloatField()
    duration_weeks = serializers.IntegerField()
    skills_taught = serializers.ListField(child=serializers.CharField())
    gap_skills_covered = serializers.IntegerField()


class RecommendationResponseSerializer(serializers.Serializer):
    """Full shape of the /api/recommend/ response."""
    career_goal = serializers.CharField()
    gap_skills = serializers.ListField(child=serializers.CharField())
    recommendations = CourseOutputSerializer(many=True)


class CourseSerializer(serializers.Serializer):
    """Generic serializer used by the course list/create API (admin/CRUD demo)."""
    id = serializers.CharField(read_only=True, required=False)
    name = serializers.CharField(max_length=200)
    category = serializers.CharField(max_length=100)
    skills_taught = serializers.ListField(child=serializers.CharField())
    rating = serializers.FloatField(default=0.0)
    duration_weeks = serializers.IntegerField(default=4)