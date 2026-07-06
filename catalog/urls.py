"""
U5 - Django: URL routing for the catalog app.
"""
from django.urls import path
from catalog import views

urlpatterns = [
    path("", views.goal_selection_view, name="goal_selection"),
    path("results/", views.recommendation_results_view, name="recommendation_results"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("about/", views.about_view, name="about"),
    path("contact/", views.contact_view, name="contact"),

    # Bookmarks, ratings, learning history
    path("bookmark/<str:course_id>/", views.bookmark_course_view, name="bookmark_course"),
    path("rate/<str:course_id>/", views.rate_course_view, name="rate_course"),
    path("my-bookmarks/", views.my_bookmarks_view, name="my_bookmarks"),
    path("my-history/", views.my_history_view, name="my_history"),

    # Admin: course management
    path("admin-courses/", views.course_list_admin_view, name="course_admin_list"),
    path("admin-courses/add/", views.course_add_view, name="course_add"),
    path("admin-courses/<str:course_id>/edit/", views.course_edit_view, name="course_edit"),
    path("admin-courses/<str:course_id>/delete/", views.course_delete_view, name="course_delete"),

    # DRF API
    path("api/recommend/", views.RecommendAPIView.as_view(), name="api_recommend"),
    path("api/courses/", views.CourseListCreateAPIView.as_view(), name="api_courses"),
]