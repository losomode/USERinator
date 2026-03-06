"""Users app configuration."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """User profiles and stub User model for FK relations."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
