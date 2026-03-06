"""Invitation models for USERinator."""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def default_expiration():
    """Default expiration: 7 days from now."""
    return timezone.now() + timedelta(days=7)


class UserInvitation(models.Model):
    """Invitation to join a company. Follows approval workflow."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        EXPIRED = "EXPIRED", "Expired"

    email = models.EmailField()
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    requested_role = models.ForeignKey(
        "roles.Role",
        on_delete=models.PROTECT,
        related_name="invitations",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    # Request info
    requested_at = models.DateTimeField(auto_now_add=True)
    requested_by_user_id = models.IntegerField(
        null=True, blank=True, help_text="AUTHinator user ID if existing user"
    )
    message = models.TextField(blank=True)

    # Review info
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_invitations",
    )
    review_notes = models.TextField(blank=True)

    # Expiration
    expires_at = models.DateTimeField(default=default_expiration)

    class Meta:
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["email", "company", "status"]),
            models.Index(fields=["status", "expires_at"]),
        ]

    def __str__(self):
        return f"{self.email} → {self.company.name} ({self.status})"

    @property
    def is_expired(self):
        return self.status == self.Status.PENDING and timezone.now() > self.expires_at

    @property
    def is_pending(self):
        return self.status == self.Status.PENDING and not self.is_expired
