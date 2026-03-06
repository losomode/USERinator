"""Companies app configuration."""

from django.apps import AppConfig


class CompaniesConfig(AppConfig):
    """Company/organization management."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "companies"
