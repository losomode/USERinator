"""Users app URL configuration."""

from django.urls import path

from users.views import (
    UserProfileBatchView,
    UserProfileDetailView,
    UserProfileListCreateView,
    UserProfileMeView,
    UserRoleView,
    UserContextView,
    PreferencesMeView,
    UserDeactivateView,
    UserMarkForDeletionView,
    UserSetCredentialsView,
    health_check,
)

app_name = "users"

urlpatterns = [
    path("health/", health_check, name="health"),
    path("me/", UserProfileMeView.as_view(), name="profile-me"),
    path("batch/", UserProfileBatchView.as_view(), name="profile-batch"),
    path("preferences/me/", PreferencesMeView.as_view(), name="preferences-me"),
    path("<int:user_id>/role/", UserRoleView.as_view(), name="user-role"),
    path("<int:user_id>/context/", UserContextView.as_view(), name="user-context"),
    path("<int:user_id>/set-credentials/", UserSetCredentialsView.as_view(), name="user-set-credentials"),
    path("<int:user_id>/deactivate/", UserDeactivateView.as_view(), name="user-deactivate"),
    path("<int:user_id>/mark-for-deletion/", UserMarkForDeletionView.as_view(), name="user-mark-for-deletion"),
    path("<int:user_id>/", UserProfileDetailView.as_view(), name="profile-detail"),
    path("", UserProfileListCreateView.as_view(), name="profile-list"),
]
