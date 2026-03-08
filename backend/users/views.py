"""User profile views for USERinator."""

import logging

from django.db.models import Q
from rest_framework import generics, status, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from companies.models import Company
from core.permissions import AdminOnly, CompanyScopedMixin, ManagerOrHigher, IsServiceAuthenticated
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

    if company_id is None:
        return None

    # Get or create a matching Company record
    company, _ = Company.objects.get_or_create(
        id=company_id,
        defaults={"name": company_name or f"Company {company_id}"},
    )

    role = getattr(user, "role", "MEMBER") or "MEMBER"
    role_level = _ROLE_LEVEL_MAP.get(role, 10)

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
        role_level = self.request.query_params.get("role_level")
        if role_level:
            queryset = queryset.filter(role_level=role_level)

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
        """Soft delete: deactivate instead of hard delete.
        
        Note: Only ADMIN can delete users. For MANAGER deactivation,
        check permissions using PermissionChecker.can_deactivate_user().
        """
        instance.is_active = False
        instance.save(update_fields=["is_active"])

    def check_object_permissions(self, request, obj):
        """Users can view/edit own profile; ADMIN/MANAGER can manage company profiles."""
        super().check_object_permissions(request, obj)
        user = request.user
        role_level = getattr(user, "role_level", 0)
        user_company = getattr(user, "company_id_remote", None)

        # ADMIN has full access to all profiles
        if role_level >= 100:
            return

        # MANAGER can view/edit users in own company
        if role_level >= 30:
            if obj.company_id != user_company:
                self.permission_denied(request)
            return

        # MEMBER can only view profiles in same company, edit own profile
        if request.method in ("GET", "HEAD", "OPTIONS"):
            # Allow viewing profiles in same company
            if obj.company_id != user_company:
                self.permission_denied(request)
        elif obj.user_id != user.id:
            # Can only edit own profile
            self.permission_denied(request)


class UserProfileMeView(views.APIView):
    """GET/PATCH own profile shortcut.  Auto-creates profile on first access."""

    permission_classes = [IsAuthenticated]

    def _get_profile(self, request):
        """Return the caller's profile, auto-provisioning if needed."""
        try:
            return UserProfile.objects.select_related("company").get(
                user_id=request.user.id
            )
        except UserProfile.DoesNotExist:
            profile = _auto_provision_profile(request.user)
            if profile is not None:
                # Re-fetch with company join
                return UserProfile.objects.select_related("company").get(
                    user_id=request.user.id
                )
            return None

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
