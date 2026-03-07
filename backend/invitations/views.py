"""Invitation views for USERinator."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import CompanyScopedMixin, ManagerOrHigher
from invitations.models import UserInvitation
from invitations.serializers import (
    InvitationCreateSerializer,
    InvitationReviewSerializer,
    InvitationSerializer,
)


class InvitationListCreateView(CompanyScopedMixin, generics.ListCreateAPIView):
    """List invitations (company-scoped for admins) or create invitation request."""

    def get_serializer_class(self):
        if self.request.method == "POST":
            return InvitationCreateSerializer
        return InvitationSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            # Only MANAGER+ can list invitations
            return [IsAuthenticated(), ManagerOrHigher()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = UserInvitation.objects.select_related("company", "requested_role")
        # Filter by status if provided
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return self.get_company_scoped_queryset(queryset)


class InvitationDetailView(generics.RetrieveAPIView):
    """Get invitation details."""

    serializer_class = InvitationSerializer
    permission_classes = [IsAuthenticated]
    queryset = UserInvitation.objects.select_related("company", "requested_role")


class InvitationApproveView(views.APIView):
    """Approve a pending invitation (MANAGER or ADMIN for own company)."""

    permission_classes = [IsAuthenticated, ManagerOrHigher]

    def post(self, request, pk):
        try:
            invitation = UserInvitation.objects.get(pk=pk)
        except UserInvitation.DoesNotExist:
            return Response(
                {"detail": "Invitation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Check company-scoped permissions (MANAGER can only approve for own company)
        role_level = getattr(request.user, "role_level", 0)
        user_company = getattr(request.user, "company_id_remote", None)
        if role_level < 100 and invitation.company_id != user_company:
            return Response(
                {"detail": "You can only approve invitations for your own company."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if invitation.status != UserInvitation.Status.PENDING:
            return Response(
                {"detail": f"Invitation is {invitation.status}, not PENDING."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invitation.is_expired:
            invitation.status = UserInvitation.Status.EXPIRED
            invitation.save(update_fields=["status"])
            return Response(
                {"detail": "Invitation has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = InvitationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invitation.status = UserInvitation.Status.APPROVED
        invitation.reviewed_at = timezone.now()
        invitation.reviewed_by = request.user
        invitation.review_notes = serializer.validated_data.get("review_notes", "")
        invitation.save()

        # Coordinate with AUTHinator for account creation
        _coordinate_with_authinator(invitation)

        # Send approval notification
        _send_status_email(invitation, "approved")

        return Response(InvitationSerializer(invitation).data)


class InvitationRejectView(views.APIView):
    """Reject a pending invitation (MANAGER or ADMIN for own company)."""

    permission_classes = [IsAuthenticated, ManagerOrHigher]

    def post(self, request, pk):
        try:
            invitation = UserInvitation.objects.get(pk=pk)
        except UserInvitation.DoesNotExist:
            return Response(
                {"detail": "Invitation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Check company-scoped permissions (MANAGER can only reject for own company)
        role_level = getattr(request.user, "role_level", 0)
        user_company = getattr(request.user, "company_id_remote", None)
        if role_level < 100 and invitation.company_id != user_company:
            return Response(
                {"detail": "You can only reject invitations for your own company."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if invitation.status != UserInvitation.Status.PENDING:
            return Response(
                {"detail": f"Invitation is {invitation.status}, not PENDING."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = InvitationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invitation.status = UserInvitation.Status.REJECTED
        invitation.reviewed_at = timezone.now()
        invitation.reviewed_by = request.user
        invitation.review_notes = serializer.validated_data.get("review_notes", "")
        invitation.save()

        # Send rejection notification
        _send_status_email(invitation, "rejected")

        return Response(InvitationSerializer(invitation).data)


def _send_status_email(invitation, action):
    """Send email notification for invitation status change."""
    try:
        send_mail(
            subject=f"Your invitation to {invitation.company.name} has been {action}",
            message=(
                f"Your invitation to join {invitation.company.name} "
                f"as {invitation.requested_role.role_name} has been {action}."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=True,
        )
    except Exception:
        pass  # Email failures should not break the workflow


logger = logging.getLogger(__name__)


def _coordinate_with_authinator(invitation):
    """Call AUTHinator to create user account after invitation approval.

    Creates a UserProfile in USERinator on success. If AUTHinator is
    unavailable, logs a warning — the profile can be created manually later.
    """
    import requests

    from users.models import UserProfile

    authinator_url = getattr(settings, "AUTHINATOR_API_URL", "")
    if not authinator_url:
        logger.info("AUTHINATOR_API_URL not configured, skipping account creation")
        return

    try:
        response = requests.post(
            f"{authinator_url}create-user/",
            json={
                "email": invitation.email,
                "role": invitation.requested_role.role_name,
                "role_level": invitation.requested_role.role_level,
                "company_id": invitation.company_id,
            },
            headers={
                "X-Service-Key": getattr(settings, "SERVICE_REGISTRATION_KEY", ""),
            },
            timeout=10,
        )
        if response.status_code == 201:
            user_data = response.json()
            UserProfile.objects.create(
                user_id=user_data["id"],
                username=user_data.get("username", invitation.email),
                email=invitation.email,
                company=invitation.company,
                display_name=user_data.get("username", invitation.email),
                role_name=invitation.requested_role.role_name,
                role_level=invitation.requested_role.role_level,
            )
            logger.info(
                "Created user %s via AUTHinator for invitation %s",
                user_data["id"],
                invitation.id,
            )
        else:
            logger.warning(
                "AUTHinator returned %s for invitation %s",
                response.status_code,
                invitation.id,
            )
    except requests.RequestException as exc:
        logger.warning(
            "Failed to reach AUTHinator for invitation %s: %s",
            invitation.id,
            exc,
        )
