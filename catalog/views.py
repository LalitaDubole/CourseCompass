"""
U5 - Django: page views (auth + goal form + results) and DRF API views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from catalog.forms import GoalSelectionForm, CourseForm
from catalog.recommender_engine import recommend_courses_for_user
from catalog.exceptions import UnknownCareerGoalError, InvalidSkillInputError
from catalog.serializers import (
    RecommendationRequestSerializer,
    RecommendationResponseSerializer,
    CourseSerializer,
)
from catalog.core_logic import normalize_skill_list
from catalog.mongo import (
    get_all_courses,
    get_course_by_id,
    create_course,
    update_course,
    delete_course,
    add_bookmark,
    remove_bookmark,
    is_bookmarked,
    get_bookmarks_for_user,
    rate_course,
    get_user_rating,
    get_learning_history,
)


# ---------------- Auth views ----------------

def register_view(request):
    error_message = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not username or not email or not password:
            error_message = "All fields are required."
        elif User.objects.filter(username=username).exists():
            error_message = "That username is already taken."
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return redirect("goal_selection")

    return render(request, "catalog/register.html", {"error_message": error_message})


def login_view(request):
    error_message = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect("course_admin_list")
            return redirect("goal_selection")
        error_message = "Invalid username or password."

    return render(request, "catalog/login.html", {"error_message": error_message})


def logout_view(request):
    logout(request)
    return redirect("login")


def about_view(request):
    return render(request, "catalog/about.html")


def contact_view(request):
    return render(request, "catalog/contact.html")


# ---------------- Regular Django pages ----------------

@login_required(login_url="login")
def goal_selection_view(request):
    """GET: show the form. POST: compute recommendations, save in session,
    then redirect to a separate results page."""
    if request.method == "POST":
        form = GoalSelectionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            skills_list = normalize_skill_list(data["current_skills"])
            try:
                result = recommend_courses_for_user(
                    name=data["name"],
                    email=data["email"],
                    career_goal=data["career_goal"],
                    raw_current_skills=skills_list,
                )
                request.session["last_result"] = result

                # U4: log this search into the user's learning history
                from catalog.mongo import add_learning_history_entry
                course_names = [c["name"] for c in result.get("recommendations", [])]
                add_learning_history_entry(
                    username=request.user.username,
                    career_goal=data["career_goal"],
                    gap_skills=result.get("gap_skills", []),
                    recommended_course_names=course_names,
                )

                return redirect("recommendation_results")
            except (UnknownCareerGoalError, InvalidSkillInputError, ValueError) as e:
                return render(
                    request,
                    "catalog/goal_form.html",
                    {"form": form, "error_message": str(e)},
                )
    else:
        form = GoalSelectionForm()

    return render(request, "catalog/goal_form.html", {"form": form, "error_message": None})


@login_required(login_url="login")
def recommendation_results_view(request):
    """Separate page that just displays whatever was last computed,
    with bookmark status and the user's own rating attached to each course."""
    result = request.session.get("last_result")

    if result:
        username = request.user.username
        # We need each course's Mongo _id to bookmark/rate it - look it up by name.
        all_courses = get_all_courses()
        name_to_id = {c["name"]: str(c["_id"]) for c in all_courses}
        for course in result.get("recommendations", []):
            course["course_id"] = name_to_id.get(course["name"], "")
            course["is_bookmarked"] = is_bookmarked(username, course["course_id"])
            course["my_rating"] = get_user_rating(username, course["course_id"])

    return render(request, "catalog/results.html", {"result": result})


@login_required(login_url="login")
def bookmark_course_view(request, course_id):
    """Toggle bookmark on/off for this course, then return to the previous page."""
    course_doc = get_course_by_id(course_id)
    if course_doc is None:
        messages.error(request, "Course not found.")
    else:
        username = request.user.username
        if is_bookmarked(username, course_id):
            remove_bookmark(username, course_id)
            messages.success(request, f"Removed '{course_doc['name']}' from bookmarks.")
        else:
            add_bookmark(username, course_id, course_doc["name"])
            messages.success(request, f"Bookmarked '{course_doc['name']}'.")

    next_url = request.POST.get("next") or request.GET.get("next") or "recommendation_results"
    return redirect(next_url)


@login_required(login_url="login")
def rate_course_view(request, course_id):
    """Submit a 1-5 star rating for a course."""
    if request.method == "POST":
        stars = request.POST.get("stars")
        course_doc = get_course_by_id(course_id)
        try:
            stars_int = int(stars)
            if 1 <= stars_int <= 5 and course_doc is not None:
                rate_course(request.user.username, course_id, stars_int)
                messages.success(request, f"You rated '{course_doc['name']}' {stars_int} star(s).")
            else:
                messages.error(request, "Invalid rating.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid rating value.")

    next_url = request.POST.get("next") or "recommendation_results"
    return redirect(next_url)


@login_required(login_url="login")
def my_bookmarks_view(request):
    """List of all courses the current student has bookmarked."""
    bookmarks = get_bookmarks_for_user(request.user.username)
    return render(request, "catalog/my_bookmarks.html", {"bookmarks": bookmarks})


@login_required(login_url="login")
def my_history_view(request):
    """List of this student's past goal searches (learning history)."""
    history = get_learning_history(request.user.username)
    return render(request, "catalog/my_history.html", {"history": history})


# ---------------- Admin: Course management (U4 CRUD + U5 Django) ----------------

def _is_staff(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(_is_staff, login_url="login")
def course_list_admin_view(request):
    """Staff-only page listing all courses with Edit/Delete links."""
    courses_raw = get_all_courses()
    for c in courses_raw:
        c["id"] = str(c["_id"])
    return render(request, "catalog/course_admin_list.html", {"courses": courses_raw})


@user_passes_test(_is_staff, login_url="login")
def course_add_view(request):
    """Staff-only page to add a new course into MongoDB."""
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            skills_list = normalize_skill_list(data["skills_taught"])
            create_course({
                "name": data["name"],
                "category": data["category"],
                "platform": data.get("platform", "Self-paced"),
                "skills_taught": skills_list,
                "rating": data["rating"],
                "duration_weeks": data["duration_weeks"],
            })
            messages.success(request, f"Course '{data['name']}' added successfully.")
            return redirect("course_admin_list")
    else:
        form = CourseForm()

    return render(request, "catalog/course_form.html", {"form": form, "mode": "Add"})


@user_passes_test(_is_staff, login_url="login")
def course_edit_view(request, course_id):
    """Staff-only page to edit an existing course."""
    course_doc = get_course_by_id(course_id)
    if course_doc is None:
        messages.error(request, "Course not found.")
        return redirect("course_admin_list")

    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            skills_list = normalize_skill_list(data["skills_taught"])
            update_course(course_id, {
                "name": data["name"],
                "category": data["category"],
                "platform": data.get("platform", "Self-paced"),
                "skills_taught": skills_list,
                "rating": data["rating"],
                "duration_weeks": data["duration_weeks"],
            })
            messages.success(request, f"Course '{data['name']}' updated successfully.")
            return redirect("course_admin_list")
    else:
        # Pre-fill the form with existing course data
        initial_data = {
            "name": course_doc.get("name", ""),
            "category": course_doc.get("category", ""),
            "platform": course_doc.get("platform", ""),
            "skills_taught": ", ".join(course_doc.get("skills_taught", [])),
            "rating": course_doc.get("rating", 0),
            "duration_weeks": course_doc.get("duration_weeks", 1),
        }
        form = CourseForm(initial=initial_data)

    return render(request, "catalog/course_form.html", {"form": form, "mode": "Edit"})


@user_passes_test(_is_staff, login_url="login")
def course_delete_view(request, course_id):
    """Staff-only: delete a course (confirm via POST)."""
    course_doc = get_course_by_id(course_id)
    if request.method == "POST":
        delete_course(course_id)
        messages.success(request, "Course deleted successfully.")
        return redirect("course_admin_list")
    return render(request, "catalog/course_confirm_delete.html", {"course": course_doc, "course_id": course_id})


# ---------------- DRF API views ----------------

class RecommendAPIView(APIView):
    """POST /api/recommend/ -> returns ranked course recommendations as JSON."""

    def post(self, request):
        req_serializer = RecommendationRequestSerializer(data=request.data)
        if not req_serializer.is_valid():
            return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = req_serializer.validated_data
        skills_list = normalize_skill_list(data["current_skills"])

        try:
            result = recommend_courses_for_user(
                name=data["name"],
                email=data["email"],
                career_goal=data["career_goal"],
                raw_current_skills=skills_list,
            )
        except (UnknownCareerGoalError, InvalidSkillInputError, ValueError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        resp_serializer = RecommendationResponseSerializer(result)
        return Response(resp_serializer.data, status=status.HTTP_200_OK)


class CourseListCreateAPIView(APIView):
    """GET /api/courses/ -> list all courses. POST /api/courses/ -> add a new course."""

    def get(self, request):
        courses_raw = get_all_courses()
        for c in courses_raw:
            c["id"] = str(c.pop("_id"))
        serializer = CourseSerializer(courses_raw, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            new_id = create_course(serializer.validated_data)
            return Response({"id": new_id, **serializer.validated_data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)