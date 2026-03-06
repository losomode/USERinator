"""Roles app configuration."""

from django.apps import AppConfig


class RolesConfig(AppConfig):
    """Role definitions and numeric level system."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "roles"
