"""
AuthinatorJWTAuthentication for USERinator.

Validates JWT tokens with AUTHinator, creates/syncs local User stubs,
and attaches role_level + company_id to request.user for permissions.
"""

import logging

from rest_framework import authentication, exceptions

from core.authinator_client import authinator_client

logger = logging.getLogger(__name__)


def _get_or_create_local_user(user_data):
    """
    Get or create a local users.User record for FK relations.

    The local User model is a stub that exists only so that
    Company.created_by, UserInvitation.reviewed_by, etc. can use real
    ForeignKey references. We sync minimal fields from AUTHinator.
    """
    from users.models import User  # late import to avoid circular deps

    authinator_id = user_data["id"]
    defaults = {
        "username": user_data["username"],
        "email": user_data.get("email", ""),
    }

    user, created = User.objects.get_or_create(
        id=authinator_id,
        defaults=defaults,
    )

    # Keep username / email in sync on subsequent logins
    if not created:
        changed = False
        for field, value in defaults.items():
            if getattr(user, field) != value:
                setattr(user, field, value)
                changed = True
        if changed:
            user.save(update_fields=list(defaults.keys()))

    return user


def _attach_userinator_attrs(user, user_data):
    """
    Attach USERinator-specific attributes to the User instance.

    These are used by permission classes and views without DB queries.
    """
    user.role = user_data.get("role", "")
    user.role_level = user_data.get("role_level", 10)
    user.company_id_remote = user_data.get("company_id")
    user.company_name = user_data.get("company_name")
    user.is_verified = user_data.get("is_verified", False)
    user.is_admin = user_data.get("role_level", 0) >= 100
    user.is_company_admin = user_data.get("role_level", 0) >= 30


class AuthinatorJWTAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication that validates JWT tokens with AUTHinator.

    1. Extracts JWT from Authorization header
    2. Validates with AUTHinator /api/auth/me/
    3. Returns local User stub with role_level, company_id attached
    """

    def authenticate(self, request):
        """Authenticate the request, returning (user, token) or None."""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header:
            return None

        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise exceptions.AuthenticationFailed("Invalid authorization header format")

        token = parts[1]

        # Validate token with AUTHinator
        user_data = authinator_client.get_user_from_token(token)

        if user_data is None:
            raise exceptions.AuthenticationFailed("Invalid or expired token")

        if not user_data.get("is_active", True):
            raise exceptions.AuthenticationFailed("User account is not active")

        # Resolve a real DB user for ForeignKey relations
        user = _get_or_create_local_user(user_data)
        _attach_userinator_attrs(user, user_data)

        return (user, token)
