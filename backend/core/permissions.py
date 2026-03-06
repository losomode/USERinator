"""
Permission classes for USERinator.

Role level hierarchy: ADMIN=100, MANAGER=30, MEMBER=10.
Company scoping ensures users only access their own company's data.
"""

from django.conf import settings
from rest_framework.permissions import BasePermission


class IsServiceAuthenticated(BasePermission):
    """Allow access if the request carries a valid internal service key.

    Services like AUTHinator use X-Service-Key to make server-to-server
    calls without a user JWT (e.g. querying role at login time).
    """

    def has_permission(self, request, view):
        key = request.META.get("HTTP_X_SERVICE_KEY", "")
        expected = getattr(settings, "INTERNAL_SERVICE_KEY", "")
        return bool(key and key == expected)


class IsCompanyAdmin(BasePermission):
    """User must be company admin or higher (role_level >= 30)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role_level", 0) >= 30
        )


class IsPlatformAdmin(BasePermission):
    """User must be platform admin (role_level >= 100)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role_level", 0) >= 100
        )


class IsOwnerOrCompanyAdmin(BasePermission):
    """User must own the resource or be a company admin for the same company."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        role_level = getattr(user, "role_level", 0)

        # Platform admins can access anything
        if role_level >= 100:
            return True

        # Company admins can access resources in their company
        if role_level >= 30:
            obj_company = getattr(obj, "company_id", None)
            user_company = getattr(user, "company_id_remote", None)
            return obj_company is not None and obj_company == user_company

        # Regular users can only access their own resources
        obj_user_id = getattr(obj, "user_id", None)
        return obj_user_id is not None and obj_user_id == user.id


class CompanyScopedMixin:
    """
    Mixin for views that filters querysets by the user's company.

    Assumes the model has a 'company' or 'company_id' field.
    Platform admins see all records.
    """

    company_field = "company_id"

    def get_company_scoped_queryset(self, queryset):
        """Filter queryset to the requesting user's company."""
        user = self.request.user
        role_level = getattr(user, "role_level", 0)

        # Platform admins see everything
        if role_level >= 100:
            return queryset

        company_id = getattr(user, "company_id_remote", None)
        if company_id is None:
            return queryset.none()

        return queryset.filter(**{self.company_field: company_id})
