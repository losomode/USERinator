"""User profile views for USERinator."""

import logging

from django.db.models import Q
from rest_framework import generics, status, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from companies.models import Company
from core.permissions import (
    AdminOnly,
    CompanyScopedMixin,
    ManagerOrHigher,
    IsServiceAuthenticated,
    PLATFORM_ROLE_THRESHOLD,
    is_platform_user,
)
from users.models import UserProfile
from permissions import PermissionChecker
from users.serializers import (
    PreferencesSerializer,
    UserProfileAdminUpdateSerializer,
    UserProfileCreateSerializer,
    UserProfileDetailSerializer,
    UserProfileListSerializer,
    UserProfileUpdateSerializer,
    UserRoleSerializer,
)

logger = logging.getLogger(__name__)

# Map AUTHinator role names → USERinator role levels
_ROLE_LEVEL_MAP = {"ADMIN": 100, "MANAGER": 30, "MEMBER": 10}


def _auto_provision_profile(user):
    """
    Auto-create a UserProfile (and Company if needed) for an authenticated
    user that doesn't have one yet.  Uses AUTHinator data attached to the
    user instance by AuthinatorJWTAuthentication.

    If a profile already exists with the same username (e.g. from demo data
    with a different user_id), adopt it by updating its user_id.

    Returns the new/adopted UserProfile or None if provisioning isn't possible.
    """
    company_id = getattr(user, "company_id_remote", None)
    company_name = getattr(user, "company_name", None)
    role = getattr(user, "role", "MEMBER") or "MEMBER"
    role_level = _ROLE_LEVEL_MAP.get(role, 10)

    company = None
    if company_id is not None:
        # Get or create a matching Company record
        company, _ = Company.objects.get_or_create(
            id=company_id,
            defaults={"name": company_name or f"Company {company_id}"},
        )
    elif role_level < PLATFORM_ROLE_THRESHOLD:
        # Company-scoped users (role < 60) must belong to a company — cannot auto-provision
        return None
    # else: platform user (role >= 60, no company) — company stays None

    # Check for an existing profile with this username (demo data scenario
    # where demo user_id != real AUTHinator id). Since user_id is the PK,
    # we must delete the old row and re-create with the correct PK.
    try:
        existing = UserProfile.objects.select_related("company").get(
            username=user.username,
        )
        if existing.user_id != user.id:
            old_company = existing.company
            old_display = existing.display_name
            old_job = existing.job_title
            old_dept = existing.department
            old_loc = existing.location
            old_phone = existing.phone
            old_bio = existing.bio
            existing.delete()
            profile = UserProfile.objects.create(
                user_id=user.id,
                username=user.username,
                email=getattr(user, "email", "") or "",
                company=old_company,
                display_name=old_display,
                job_title=old_job,
                department=old_dept,
                location=old_loc,
                phone=old_phone,
                bio=old_bio,
                role_name=role,
                role_level=role_level,
            )
            logger.info(
                "Adopted existing profile '%s' for AUTHinator user id=%s",
                user.username,
                user.id,
            )
            return profile
        # user_id already matches — just return the existing profile
        return existing
    except UserProfile.DoesNotExist:
        pass

    profile = UserProfile.objects.create(
        user_id=user.id,
        username=user.username,
        email=getattr(user, "email", ""),
        company=company,
        display_name=getattr(user, "display_name", None) or user.username,
        role_name=role,
        role_level=role_level,
    )
    logger.info("Auto-provisioned profile for user %s (id=%s)", user.username, user.id)
    return profile


def _deactivate_authinator_account(user_id: int) -> None:
    """Call AUTHinator to deactivate the user's login account.

    Uses the service key so this works even during background operations.
    Failures are logged as warnings — the USERinator soft-delete still proceeds.
    """
    import requests
    from django.conf import settings as _settings

    authinator_url = getattr(_settings, "AUTHINATOR_API_URL", "")
    if not authinator_url:
        logger.warning(
            "AUTHINATOR_API_URL not configured — skipping AUTHinator deactivation for user %s",
            user_id,
        )
        return

    try:
        # AUTHINATOR_API_URL ends with 'auth/' (e.g. http://localhost:8001/api/auth/)
        # so appending 'admin/deactivate-user/' gives the correct endpoint path.
        response = requests.post(
            f"{authinator_url}admin/deactivate-user/",
            json={"user_id": user_id},
            headers={"X-Service-Key": getattr(_settings, "SERVICE_REGISTRATION_KEY", "")},
            timeout=10,
        )
        if response.status_code == 200:
            logger.info("AUTHinator account deactivated for user_id=%s", user_id)
        else:
            logger.warning(
                "AUTHinator deactivation returned %s for user_id=%s: %s",
                response.status_code,
                user_id,
                response.text,
            )
    except requests.RequestException as exc:
        logger.warning(
            "Could not reach AUTHinator to deactivate user_id=%s: %s", user_id, exc
        )


class UserProfileListCreateView(CompanyScopedMixin, generics.ListCreateAPIView):
    """List user profiles (company-scoped) or create new profile (admin)."""

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserProfileCreateSerializer
        return UserProfileListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            # ADMIN can create any role, MANAGER can create MEMBER only
            return [IsAuthenticated(), ManagerOrHigher()]
        return [IsAuthenticated()]

    def get_queryset(self):
        role_level = getattr(self.request.user, "role_level", 0)
        # Members (< 30) only see active users.
        # Managers/admins (>= 30) see active + deactivated so they can manage their team.
        if role_level >= 30:
            queryset = UserProfile.objects.select_related("company")
        else:
            queryset = UserProfile.objects.select_related("company").filter(is_active=True)
        queryset = self.get_company_scoped_queryset(queryset)

        # Search support
        search = self.request.query_params.get("search", "")
        if search:
            queryset = queryset.filter(
                Q(display_name__icontains=search)
                | Q(email__icontains=search)
                | Q(job_title__icontains=search)
                | Q(username__icontains=search)
            )

        # Role level filter
        role_level_filter = self.request.query_params.get("role_level")
        if role_level_filter:
            queryset = queryset.filter(role_level=role_level_filter)

        # Company filter (platform users only — admin or no-company platform roles)
        company_filter = self.request.query_params.get("company")
        if company_filter and is_platform_user(self.request.user):
            queryset = queryset.filter(company_id=company_filter)

        return queryset


class UserProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or deactivate a user profile."""

    lookup_field = "user_id"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            if getattr(self.request.user, "role_level", 0) >= 30:
                return UserProfileAdminUpdateSerializer
            return UserProfileUpdateSerializer
        return UserProfileDetailSerializer

    def get_permissions(self):
        if self.request.method == "DELETE":
            # Only ADMIN can delete, MANAGER can deactivate via PermissionChecker
            return [IsAuthenticated(), AdminOnly()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return UserProfile.objects.select_related("company")

    def perform_destroy(self, instance):
        """Full user removal.

        Two paths depending on state:

        A) User already deactivated + marked_for_deletion (admin final review step):
           Hard-delete the UserProfile row. AUTHinator was already deactivated when
           the user was first soft-deactivated, so no extra call needed.

        B) Regular removal (first-time delete of an active user):
           Deactivate AUTHinator, soft-delete profile, mangle username to free the slot.
        """
        if not instance.is_active and instance.marked_for_deletion:
            # Path A: permanent deletion — remove the DB row entirely
            display = instance.display_name
            uid = instance.user_id
            instance.delete()
            logger.info("Permanently deleted user '%s' (id=%s).", display, uid)
            return

        # Path B: first-time removal — deactivate auth + soft-delete profile
        _deactivate_authinator_account(instance.user_id)
        instance.is_active = False
        if not instance.username.startswith("_deleted_"):
            instance.username = f"_deleted_{instance.user_id}_{instance.username}"
        instance.save(update_fields=["is_active", "username"])
        logger.info(
            "Deactivated user %s (id=%s) — AUTHinator deactivated, profile soft-deleted.",
            instance.username,
            instance.user_id,
        )

    def check_object_permissions(self, request, obj):
        """Users can view/edit own profile; ADMIN/MANAGER can manage company profiles."""
        super().check_object_permissions(request, obj)
        user = request.user
        role_level = getattr(user, "role_level", 0)
        user_company = getattr(user, "company_id_remote", None)

        # ADMIN has full access to all profiles
        if role_level >= 100:
            return

        # Platform users (no company, role >= 60): cross-company READ-ONLY
        # They can view any profile but cannot edit others' profiles
        if is_platform_user(user):
            if request.method not in ("GET", "HEAD", "OPTIONS"):
                # Allow editing only own profile
                if obj.user_id != user.id:
                    self.permission_denied(request)
            return

        # Company-scoped users (30-99): view their company; write only to lower-level users
        if role_level >= 30:
            if obj.company_id != user_company:
                self.permission_denied(request)
            # Write operations: cannot edit peers (same level) or superiors
            if request.method not in ("GET", "HEAD", "OPTIONS"):
                if obj.role_level >= role_level:
                    self.permission_denied(
                        request,
                        message="You can only edit users with a lower role level than your own.",
                    )
            return

        # MEMBER can only view profiles in same company, edit own profile
        if request.method in ("GET", "HEAD", "OPTIONS"):
            if obj.company_id != user_company:
                self.permission_denied(request)
        elif obj.user_id != user.id:
            self.permission_denied(request)


class UserProfileMeView(views.APIView):
    """GET/PATCH own profile shortcut.  Auto-creates profile on first access."""

    permission_classes = [IsAuthenticated]

    def _get_profile(self, request):
        """Return the caller's profile, auto-provisioning if needed.

        Also syncs username/email from AUTHinator token when they drift
        (e.g. after a username change via /api/auth/change-username/).
        """
        try:
            profile = UserProfile.objects.select_related("company").get(
                user_id=request.user.id
            )
        except UserProfile.DoesNotExist:
            profile = _auto_provision_profile(request.user)
            if profile is not None:
                # Re-fetch with company join
                profile = UserProfile.objects.select_related("company").get(
                    user_id=request.user.id
                )
            return profile

        # Sync username / email if AUTHinator changed them
        update_fields = []
        if request.user.username and profile.username != request.user.username:
            profile.username = request.user.username
            update_fields.append("username")
        token_email = getattr(request.user, "email", "") or ""
        if token_email and profile.email != token_email:
            profile.email = token_email
            update_fields.append("email")
        if update_fields:
            profile.save(update_fields=update_fields)
        return profile

    def get(self, request):
        profile = self._get_profile(request)
        if profile is None:
            return Response(
                {"detail": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = UserProfileDetailSerializer(profile, context={"request": request})
        response = Response(serializer.data)
        # Prevent browser caching of user profiles
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    def patch(self, request):
        profile = self._get_profile(request)
        if profile is None:
            return Response(
                {"detail": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = UserProfileUpdateSerializer(
            profile, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserProfileBatchView(CompanyScopedMixin, views.APIView):
    """Batch fetch profiles by user_ids."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_ids = request.data.get("user_ids", [])
        if not isinstance(user_ids, list) or len(user_ids) > 100:
            return Response(
                {"detail": "Provide a list of 1-100 user_ids."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = UserProfile.objects.select_related("company").filter(
            user_id__in=user_ids, is_active=True
        )
        queryset = self.get_company_scoped_queryset(queryset)
        serializer = UserProfileListSerializer(queryset, many=True)
        return Response(serializer.data)


class UserRoleView(views.APIView):
    """Internal endpoint for AUTHinator to query user role.

    Accepts either Bearer token (IsAuthenticated) or X-Service-Key
    header for server-to-server calls at login time.
    """

    permission_classes = [IsAuthenticated | IsServiceAuthenticated]

    def get(self, request, user_id):
        try:
            profile = UserProfile.objects.get(user_id=user_id, is_active=True)
        except UserProfile.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = UserRoleSerializer(profile)
        return Response(serializer.data)


class UserContextView(views.APIView):
    """Complete user context for service authorization.
    
    Returns company_id, company_name, role_name, role_level for the specified user.
    
    This endpoint is used by all services (RMAinator, FULFILinator, etc.) to
    get authorization context after validating the JWT. Response is cached for
    5 minutes to minimize database queries.
    
    Accepts either Bearer token (IsAuthenticated) or X-Service-Key header for
    server-to-server calls.
    """

    permission_classes = [IsAuthenticated | IsServiceAuthenticated]

    def get(self, request, user_id):
        from users.serializers import UserContextSerializer
        
        # Fetch from database (no caching - user context must be real-time)
        try:
            profile = UserProfile.objects.select_related("company").get(
                user_id=user_id, is_active=True
            )
        except UserProfile.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        serializer = UserContextSerializer(profile)
        data = serializer.data
        
        # Add permissions for frontend
        checker = PermissionChecker(
            user_id=profile.user_id,
            role_level=profile.role_level,
            company_id=profile.company_id if profile.company else None
        )
        data['permissions'] = checker.get_permissions_dict()
        
        response = Response(data)
        # Prevent browser caching of context data
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response


class PreferencesMeView(views.APIView):
    """GET/PATCH own preferences.  Reuses auto-provisioning from UserProfileMeView."""

    permission_classes = [IsAuthenticated]

    def _get_profile(self, request):
        try:
            return UserProfile.objects.get(user_id=request.user.id)
        except UserProfile.DoesNotExist:
            return _auto_provision_profile(request.user)

    def get(self, request):
        profile = self._get_profile(request)
        if profile is None:
            return Response(
                {"detail": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = PreferencesSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        profile = self._get_profile(request)
        if profile is None:
            return Response(
                {"detail": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = PreferencesSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Deactivation & deletion-request workflow
# ---------------------------------------------------------------------------

# Minimum role level to have deactivation rights over company users
_DEACTIVATE_MIN_LEVEL = 30  # COMPANY_MANAGER+


class UserSetCredentialsView(views.APIView):
    """Allow higher-level users to change a lower-level user's password and/or username.

    Permission rules mirror deactivation: acting user must have higher role_level
    than the target and be in the same company (or be a platform admin).

    Accepts: { password?: str, new_username?: str } — one or both.
    Proxies to AUTHinator via service key after permission checks.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        import requests as _requests
        from django.conf import settings as _settings

        acting_level = getattr(request.user, "role_level", 0)
        acting_company = getattr(request.user, "company_id_remote", None)

        if acting_level < 30:
            return Response(
                {"detail": "You do not have permission to change another user's credentials."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            profile = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if acting_level < 100 and profile.company_id != acting_company:
            return Response(
                {"detail": "You can only update credentials of users within your company."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if acting_level < 100 and profile.role_level >= acting_level:
            return Response(
                {"detail": "You can only update credentials of users with a lower role level than your own."},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_password = request.data.get("password", "").strip()
        new_username = request.data.get("new_username", "").strip()

        if not new_password and not new_username:
            return Response(
                {"detail": "Provide at least one of: password, new_username."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        authinator_url = getattr(_settings, "AUTHINATOR_API_URL", "")
        service_key = getattr(_settings, "SERVICE_REGISTRATION_KEY", "")
        headers = {"X-Service-Key": service_key}
        errors = []

        if new_password:
            try:
                resp = _requests.post(
                    f"{authinator_url}admin/set-password/",
                    json={"user_id": user_id, "new_password": new_password},
                    headers=headers,
                    timeout=10,
                )
                if resp.status_code != 200:
                    errors.append(resp.json().get("detail") or "Password update failed.")
            except _requests.RequestException as exc:
                errors.append(f"Could not reach AUTHinator: {exc}")

        if new_username and not errors:
            try:
                resp = _requests.post(
                    f"{authinator_url}admin/set-username/",
                    json={"user_id": user_id, "new_username": new_username},
                    headers=headers,
                    timeout=10,
                )
                if resp.status_code == 200:
                    # Sync username in USERinator profile
                    profile.username = new_username
                    profile.save(update_fields=["username"])
                else:
                    errors.append(resp.json().get("detail") or "Username update failed.")
            except _requests.RequestException as exc:
                errors.append(f"Could not reach AUTHinator: {exc}")

        if errors:
            return Response({"detail": " ".join(errors)}, status=status.HTTP_400_BAD_REQUEST)

        parts = []
        if new_password:
            parts.append("password")
        if new_username:
            parts.append(f"username (now: {new_username})")
        return Response({"detail": f"Updated {' and '.join(parts)} successfully."})


class UserDeactivateView(views.APIView):
    """Deactivate a user account within a company.

    Permission rules (all company-scoped):
    - COMPANY_MANAGER (30): can deactivate COMPANY_MEMBER (10) only
    - COMPANY_ADMIN (50): can deactivate COMPANY_MANAGER (30) and COMPANY_MEMBER (10)
    - PLATFORM_ADMIN (100): can deactivate anyone (but they use full Remove for that)

    Deactivation: sets UserProfile.is_active=False AND deactivates the AUTHinator
    account so the user can no longer log in.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        acting_level = getattr(request.user, "role_level", 0)
        acting_company = getattr(request.user, "company_id_remote", None)

        if acting_level < _DEACTIVATE_MIN_LEVEL:
            return Response(
                {"detail": "You do not have permission to deactivate users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            profile = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Company scoping (platform admins skip this)
        if acting_level < 100 and profile.company_id != acting_company:
            return Response(
                {"detail": "You can only deactivate users within your company."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Cannot deactivate peers or superiors
        if acting_level < 100 and profile.role_level >= acting_level:
            return Response(
                {"detail": "You can only deactivate users with a lower role level than your own."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not profile.is_active:
            return Response(
                {"detail": "User is already deactivated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Deactivate AUTHinator account first (revokes login + JWTs)
        _deactivate_authinator_account(user_id)

        # Soft-deactivate the USERinator profile (keep username intact for review)
        profile.is_active = False
        profile.save(update_fields=["is_active"])

        logger.info(
            "User %s (id=%s) deactivated by %s (level=%s)",
            profile.username, user_id, request.user.username, acting_level,
        )
        return Response({"detail": f"{profile.display_name} has been deactivated."})


class UserMarkForDeletionView(views.APIView):
    """Mark a deactivated user for permanent deletion.

    Any user with deactivation rights can mark a deactivated user.
    Platform admins (100) review and permanently delete via the DELETE endpoint.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        from django.utils import timezone as tz

        acting_level = getattr(request.user, "role_level", 0)
        acting_company = getattr(request.user, "company_id_remote", None)

        if acting_level < _DEACTIVATE_MIN_LEVEL:
            return Response(
                {"detail": "You do not have permission to mark users for deletion."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            profile = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if acting_level < 100 and profile.company_id != acting_company:
            return Response(
                {"detail": "You can only mark users within your company for deletion."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if acting_level < 100 and profile.role_level >= acting_level:
            return Response(
                {"detail": "You can only mark users with a lower role level than your own."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if profile.is_active:
            return Response(
                {"detail": "Deactivate the user before marking them for deletion."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.marked_for_deletion = True
        profile.marked_for_deletion_at = tz.now()
        profile.save(update_fields=["marked_for_deletion", "marked_for_deletion_at"])

        logger.info(
            "User %s (id=%s) marked for deletion by %s (level=%s)",
            profile.username, user_id, request.user.username, acting_level,
        )
        return Response({"detail": f"{profile.display_name} has been marked for deletion and will be reviewed by a platform admin."})


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint with database connectivity test."""
    from django.db import connection
    from django.utils import timezone

    db_ok = True
    try:
        connection.ensure_connection()
    except Exception:
        db_ok = False

    data = {
        "status": "healthy" if db_ok else "degraded",
        "service": "USERinator",
        "version": "1.0.0",
        "timestamp": timezone.now().isoformat(),
        "database": "connected" if db_ok else "unavailable",
    }
    status_code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(data, status=status_code)
