"""Company models for USERinator."""

from django.conf import settings
from django.db import models


class Company(models.Model):
    """Company/organization that users belong to."""

    # Core info
    name = models.CharField(max_length=255, unique=True)

    # Standard business info
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(
        max_length=50, blank=True, help_text='e.g. "1-10", "11-50", "51-200"'
    )
    logo_url = models.URLField(blank=True)
    billing_contact_email = models.EmailField(blank=True)

    # Extended metadata
    custom_fields = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True, help_text="List of tag strings")
    notes = models.TextField(blank=True, help_text="Admin-only notes")

    class AccountStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        ARCHIVED = "archived", "Archived"

    account_status = models.CharField(
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.ACTIVE,
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_companies",
    )

    class Meta:
        verbose_name_plural = "companies"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["account_status"]),
        ]

    def __str__(self):
        return self.name
