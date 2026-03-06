"""Role views for USERinator."""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsPlatformAdmin
from roles.models import Role
from roles.serializers import RoleCreateSerializer, RoleSerializer, RoleUpdateSerializer


class RoleListCreateView(generics.ListCreateAPIView):
    """List roles or create custom role (platform admin)."""

    queryset = Role.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return RoleCreateSerializer
        return RoleSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsPlatformAdmin()]
        return [IsAuthenticated()]


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a role definition."""

    queryset = Role.objects.all()

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return RoleUpdateSerializer
        return RoleSerializer

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsAuthenticated(), IsPlatformAdmin()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        if instance.is_system_role:
            return Response(
                {"detail": "System roles cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_system_role:
            return Response(
                {"detail": "System roles cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
