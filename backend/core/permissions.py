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


class IsAuthenticatedOrServiceKey(BasePermission):
    """Allow access if user is authenticated OR request has valid service key.
    
    This allows both user requests (with JWT) and service-to-service requests
    (with X-Service-Key header) to access the same endpoint.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated
        if request.user and request.user.is_authenticated:
            return True
        
        # Check if service key is valid
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


class AdminOnly(BasePermission):
    """Require ADMIN role (level >= 100).
    
    Used for actions that only platform administrators can perform:
    - Creating companies
    - Deleting users
    - Changing user roles
    - Editing RMAs, POs, Orders, Deliveries
    - Managing Items
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role_level", 0) >= 100
        )


class ManagerOrHigher(BasePermission):
    """Require MANAGER role or higher (level >= 30).
    
    Used for actions that managers and admins can perform:
    - Editing company info (with company scoping)
    - Editing user profiles (with company scoping)
    - Approving invitations (with company scoping)
    - Deactivating users (with company scoping)
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role_level", 0) >= 30
        )


class CanViewCompanyScopedResource(BasePermission):
    """User can view resources scoped to their company.
    
    All authenticated users can view, but queryset filtering
    should limit to own company (except ADMIN sees all).
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
