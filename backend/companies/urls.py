"""Companies app URL configuration."""

from django.urls import path

from companies.views import (
    CompanyDetailView,
    CompanyListCreateView,
    CompanyMyView,
    CompanyUsersView,
)

app_name = "companies"

urlpatterns = [
    path("my/", CompanyMyView.as_view(), name="company-my"),
    path("<int:pk>/users/", CompanyUsersView.as_view(), name="company-users"),
    path("<int:pk>/", CompanyDetailView.as_view(), name="company-detail"),
    path("", CompanyListCreateView.as_view(), name="company-list"),
]
