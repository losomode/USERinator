"""Users app URL configuration."""

from django.urls import path

from users.views import (
    UserProfileBatchView,
    UserProfileDetailView,
    UserProfileListCreateView,
    UserProfileMeView,
    UserRoleView,
    PreferencesMeView,
    health_check,
)

app_name = "users"

urlpatterns = [
    path("health/", health_check, name="health"),
    path("me/", UserProfileMeView.as_view(), name="profile-me"),
    path("batch/", UserProfileBatchView.as_view(), name="profile-batch"),
    path("preferences/me/", PreferencesMeView.as_view(), name="preferences-me"),
    path("<int:user_id>/role/", UserRoleView.as_view(), name="user-role"),
    path("<int:user_id>/", UserProfileDetailView.as_view(), name="profile-detail"),
    path("", UserProfileListCreateView.as_view(), name="profile-list"),
]
