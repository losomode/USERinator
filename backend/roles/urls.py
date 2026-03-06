"""Roles app URL configuration."""

from django.urls import path

from roles.views import RoleDetailView, RoleListCreateView

app_name = "roles"

urlpatterns = [
    path("<int:pk>/", RoleDetailView.as_view(), name="role-detail"),
    path("", RoleListCreateView.as_view(), name="role-list"),
]
