"""Invitations app configuration."""

from django.apps import AppConfig


class InvitationsConfig(AppConfig):
    """User invitation and approval workflow."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "invitations"
