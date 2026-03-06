"""
User models for USERinator.

Contains the stub User model (for AUTH_USER_MODEL FK relations) and
the UserProfile model (full profile data, source of truth for user info).
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Minimal user model for database foreign key relations.

    This is a stub model that maintains database FK integrity.
    Actual authentication is handled by AUTHinator.
    The full user profile data lives in UserProfile.
    """

    class Meta:
        db_table = "users_user"

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    """
    Extended user profile — source of truth for user data in USERinator.

    user_id is synced from AUTHinator (matches AUTHinator User.id).
    Each user belongs to exactly one company.
    """

    # Synced from AUTHinator (stub pattern)
    user_id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField()

    # Company relationship
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.PROTECT,
        related_name="user_profiles",
    )

    # Profile data
    display_name = models.CharField(max_length=255)
    avatar_url = models.URLField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=255, blank=True)

    # Role (numeric level system)
    role_name = models.CharField(max_length=50, default="MEMBER")
    role_level = models.IntegerField(default=10)

    # Preferences
    timezone = models.CharField(max_length=50, default="UTC")
    language = models.CharField(max_length=10, default="en")
    notification_email = models.BooleanField(default=True)
    notification_in_app = models.BooleanField(default=True)

    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_name"]
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["role_level"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return f"{self.display_name} ({self.username})"

    @property
    def is_admin(self):
        return self.role_level >= 100

    @property
    def is_company_admin(self):
        return self.role_level >= 30
