"""Company views for USERinator."""

from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from companies.models import Company
from companies.serializers import (
    CompanyCreateSerializer,
    CompanyDetailSerializer,
    CompanyListSerializer,
    CompanyUpdateSerializer,
)
from core.permissions import IsCompanyAdmin, IsPlatformAdmin
from users.models import UserProfile
from users.serializers import UserProfileListSerializer


class CompanyListCreateView(generics.ListCreateAPIView):
    """List companies (admin) or create company (platform admin)."""

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CompanyCreateSerializer
        return CompanyListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsPlatformAdmin()]
        return [IsAuthenticated(), IsPlatformAdmin()]

    def get_queryset(self):
        return Company.objects.all()


class CompanyDetailView(generics.RetrieveUpdateAPIView):
    """Get or update company details."""

    queryset = Company.objects.all()

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return CompanyUpdateSerializer
        return CompanyDetailSerializer

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH"):
            return [IsAuthenticated(), IsCompanyAdmin()]
        return [IsAuthenticated()]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        role_level = getattr(request.user, "role_level", 0)
        if role_level >= 100:
            return
        # Company admins can only update their own company
        if request.method in ("PUT", "PATCH"):
            user_company = getattr(request.user, "company_id_remote", None)
            if obj.id != user_company:
                self.permission_denied(request)


class CompanyUsersView(generics.ListAPIView):
    """List users in a specific company."""

    serializer_class = UserProfileListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        company_id = self.kwargs["pk"]
        user = self.request.user
        role_level = getattr(user, "role_level", 0)

        # Platform admins can see any company's users
        if role_level >= 100:
            return UserProfile.objects.filter(company_id=company_id, is_active=True)

        # Others can only see their own company's users
        user_company = getattr(user, "company_id_remote", None)
        if user_company != company_id:
            return UserProfile.objects.none()

        return UserProfile.objects.filter(company_id=company_id, is_active=True)


class CompanyMyView(views.APIView):
    """Get own company shortcut."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        company_id = getattr(request.user, "company_id_remote", None)
        if company_id is None:
            return Response(
                {"detail": "No company associated."},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {"detail": "Company not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CompanyDetailSerializer(company, context={"request": request})
        return Response(serializer.data)
