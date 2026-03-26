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
    Attach initial role/company attributes from AUTHinator token data.

    NOTE: AUTHinator only knows two roles: ADMIN and USER.  All fine-grained
    USERinator roles (PLATFORM_ADMIN=100, COMPANY_MANAGER=30, etc.) are stored
    in the UserProfile.  Call _enrich_from_userprofile() afterwards to override
    these attrs with the authoritative values from the UserProfile.
    """
    user.role = user_data.get("role", "")
    user.role_level = user_data.get("role_level", 10)
    user.company_id_remote = user_data.get("company_id")
    user.company_name = user_data.get("company_name")
    user.is_verified = user_data.get("is_verified", False)
    user.is_admin = user_data.get("role_level", 0) >= 100
    user.is_company_admin = user_data.get("role_level", 0) >= 30


def _enrich_from_userprofile(user) -> None:
    """Override role/company attrs from the USERinator UserProfile.

    UserProfile is the single source of truth for role_level and company.
    AUTHinator only carries a coarse ADMIN/USER distinction; every nuanced
    role (PLATFORM_ADMIN, PLATFORM_MANAGER, COMPANY_MANAGER, …) lives here.

    Falls back silently to AUTHinator-derived attrs when no active profile
    exists yet (e.g. first request before auto-provision has run).
    """
    from users.models import UserProfile  # late import — avoids circular deps
    from core.permissions import PLATFORM_ROLE_THRESHOLD

    try:
        profile = UserProfile.objects.select_related("company").get(
            user_id=user.id, is_active=True
        )
    except UserProfile.DoesNotExist:
        # Profile not provisioned yet — keep the AUTHinator-derived attrs.
        return
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to enrich user %s from UserProfile: %s", user.id, exc)
        return

    user.role = profile.role_name
    user.role_level = profile.role_level
    user.company_id_remote = profile.company_id if profile.company_id else None
    user.company_name = profile.company.name if profile.company else None
    user.is_admin = profile.role_level >= 100
    user.is_company_admin = profile.role_level >= 30
    user.is_platform_user = (
        profile.role_level >= PLATFORM_ROLE_THRESHOLD and not profile.company_id
    )


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
        _attach_userinator_attrs(user, user_data)  # initial attrs from AUTHinator
        _enrich_from_userprofile(user)              # override with authoritative USERinator data

        return (user, token)
