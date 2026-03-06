"""Core app configuration."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Core app for authentication, permissions, and shared utilities."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
