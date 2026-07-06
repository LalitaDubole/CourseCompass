"""
U5 - Django: forms for goal-selection and course management (admin).
"""
from django import forms
from catalog.core_logic import get_supported_goals


class GoalSelectionForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Your name"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "you@example.com"}),
    )
    career_goal = forms.ChoiceField(
        choices=[],  # populated in __init__ so it always reflects core_logic's dict
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    current_skills = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "e.g. python, sql, excel"}
        ),
        help_text="Comma-separated list of skills you already have.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        goals = get_supported_goals()
        self.fields["career_goal"].choices = [(g, g) for g in goals]


class CourseForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Course name"}),
    )
    category = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Data, Web Dev"}),
    )
    platform = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Coursera, Udemy, Self-paced"}),
    )
    skills_taught = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. python, sql"}),
        help_text="Comma-separated list of skills this course teaches.",
    )
    rating = forms.FloatField(
        min_value=0, max_value=5,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
    )
    duration_weeks = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    