"""User profile views for USERinator."""

from django.db.models import Q
from rest_framework import generics, status, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.permissions import CompanyScopedMixin, IsCompanyAdmin, IsServiceAuthenticated
from users.models import UserProfile
from users.serializers import (
    PreferencesSerializer,
    UserProfileAdminUpdateSerializer,
    UserProfileCreateSerializer,
    UserProfileDetailSerializer,
    UserProfileListSerializer,
    UserProfileUpdateSerializer,
    UserRoleSerializer,
)


class UserProfileListCreateView(CompanyScopedMixin, generics.ListCreateAPIView):
    """List user profiles (company-scoped) or create new profile (admin)."""

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserProfileCreateSerializer
        return UserProfileListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCompanyAdmin()]
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
            return [IsAuthenticated(), IsCompanyAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return UserProfile.objects.select_related("company")

    def perform_destroy(self, instance):
        """Soft delete: deactivate instead of hard delete."""
        instance.is_active = False
        instance.save(update_fields=["is_active"])

    def check_object_permissions(self, request, obj):
        """Users can view/edit own profile; admins can manage company profiles."""
        super().check_object_permissions(request, obj)
        user = request.user
        role_level = getattr(user, "role_level", 0)

        if role_level >= 100:
            return  # Platform admin: full access

        if role_level >= 30:
            user_company = getattr(user, "company_id_remote", None)
            if obj.company_id != user_company:
                self.permission_denied(request)
            return

        # Regular users can only access their own profile
        if request.method in ("GET", "HEAD", "OPTIONS"):
            # Allow viewing profiles in same company
            user_company = getattr(user, "company_id_remote", None)
            if obj.company_id != user_company:
                self.permission_denied(request)
        elif obj.user_id != user.id:
            self.permission_denied(request)


class UserProfileMeView(views.APIView):
    """GET/PATCH own profile shortcut."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = UserProfile.objects.select_related("company").get(
                user_id=request.user.id
            )
        except UserProfile.DoesNotExist:
            return Response(
                {"detail": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = UserProfileDetailSerializer(profile, context={"request": request})
        return Response(serializer.data)

    def patch(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user.id)
        except UserProfile.DoesNotExist:
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


class PreferencesMeView(views.APIView):
    """GET/PATCH own preferences."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user.id)
        except UserProfile.DoesNotExist:
            return Response(
                {"detail": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = PreferencesSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user.id)
        except UserProfile.DoesNotExist:
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
