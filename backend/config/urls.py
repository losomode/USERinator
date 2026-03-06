"""USERinator URL configuration."""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),
    path("api/companies/", include("companies.urls")),
    path("api/roles/", include("roles.urls")),
    path("api/invitations/", include("invitations.urls")),
]
