"""Role models for USERinator."""

from django.conf import settings
from django.db import models


class Role(models.Model):
    """Role definition with numeric level for permission checks."""

    role_name = models.CharField(max_length=50, unique=True)
    role_level = models.IntegerField(unique=True, help_text="Numeric level (1-100)")
    description = models.TextField(blank=True)
    is_system_role = models.BooleanField(
        default=False,
        help_text="True for built-in roles (ADMIN, MANAGER, MEMBER)",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_roles",
    )

    class Meta:
        ordering = ["-role_level"]

    def __str__(self):
        return f"{self.role_name} (level {self.role_level})"
