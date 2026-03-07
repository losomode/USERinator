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
from core.permissions import AdminOnly, CanViewCompanyScopedResource, ManagerOrHigher, IsAuthenticatedOrServiceKey
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
            # Only ADMIN can create companies
            return [IsAuthenticated(), AdminOnly()]
        # Only ADMIN can list all companies
        return [IsAuthenticated(), AdminOnly()]

    def get_queryset(self):
        # ADMIN sees all companies
        return Company.objects.all()


class CompanyDetailView(generics.RetrieveUpdateAPIView):
    """Get or update company details.
    
    Accepts either Bearer token (IsAuthenticated) or X-Service-Key header
    for server-to-server calls.
    """

    queryset = Company.objects.all()

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return CompanyUpdateSerializer
        return CompanyDetailSerializer

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH"):
            # ADMIN can edit all, MANAGER can edit own company
            return [IsAuthenticated(), ManagerOrHigher()]
        # View: authenticated users or service key
        return [IsAuthenticatedOrServiceKey()]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        
        # Service key authentication bypasses company scoping (used for service-to-service calls)
        if not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
            return
        
        role_level = getattr(request.user, "role_level", 0)
        
        # ADMIN can access any company
        if role_level >= 100:
            return
        
        # MANAGER/MEMBER can only view their own company
        user_company = getattr(request.user, "company_id_remote", None)
        if obj.id != user_company:
            self.permission_denied(request)
        
        # Only MANAGER can edit (MEMBER blocked by ManagerOrHigher permission)
        # MANAGER can only edit their own company (already checked above)


class CompanyUsersView(generics.ListAPIView):
    """List users in a specific company."""

    serializer_class = UserProfileListSerializer
    permission_classes = [IsAuthenticated, CanViewCompanyScopedResource]

    def get_queryset(self):
        company_id = self.kwargs["pk"]
        user = self.request.user
        role_level = getattr(user, "role_level", 0)

        # ADMIN can see any company's users
        if role_level >= 100:
            return UserProfile.objects.filter(company_id=company_id, is_active=True)

        # MANAGER/MEMBER can only see their own company's users
        user_company = getattr(user, "company_id_remote", None)
        if user_company != int(company_id):
            return UserProfile.objects.none()

        return UserProfile.objects.filter(company_id=company_id, is_active=True)


class CompanyMyView(views.APIView):
    """Get own company shortcut."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        company_id = getattr(request.user, "company_id_remote", None)
        # Fall back to UserProfile company when AUTHinator doesn't provide one
        if company_id is None:
            try:
                profile = UserProfile.objects.get(user_id=request.user.id)
                company_id = profile.company_id
            except UserProfile.DoesNotExist:
                pass
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
