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

    def create(self, request, *args, **kwargs):
        """Create invitation, auto-approving immediately if the requester is an admin."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role_level = getattr(request.user, "role_level", 0)

        if role_level >= 100:
            # Admin — skip the review queue and provision the account straight away.
            invitation = serializer.save(
                status=UserInvitation.Status.APPROVED,
                requested_by_user_id=request.user.id,
                reviewed_at=timezone.now(),
                reviewed_by=request.user,
                review_notes="Auto-approved by admin",
            )
            provisioned = _coordinate_with_authinator(invitation)
            response_data = InvitationSerializer(invitation).data
            if provisioned:
                response_data["provisioned_user"] = {
                    "username": provisioned["username"],
                    "temp_password": provisioned["temp_password"],
                    "note": "Account created. Share these credentials with the user. They should change their password on first login.",
                }
            else:
                response_data["provisioned_user"] = None
                response_data["provision_error"] = (
                    "Account creation in AUTHinator failed. "
                    "Use \"Create User\" to provision manually."
                )
        else:
            # Manager — standard pending flow, requires admin review.
            invitation = serializer.save(requested_by_user_id=request.user.id)
            response_data = InvitationSerializer(invitation).data

        headers = self.get_success_headers(response_data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


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

        # Coordinate with AUTHinator for account creation.
        # Returns {username, temp_password} on success, None on failure.
        provisioned = _coordinate_with_authinator(invitation)

        response_data = InvitationSerializer(invitation).data
        if provisioned:
            response_data["provisioned_user"] = {
                "username": provisioned["username"],
                "temp_password": provisioned["temp_password"],
                "note": "Account created. Share these credentials with the user. They should change their password on first login.",
            }
        else:
            response_data["provisioned_user"] = None
            response_data["provision_error"] = (
                "Account creation in AUTHinator failed or is pending. "
                "Use \"Create User\" to provision manually."
            )

        return Response(response_data)


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
    """Call AUTHinator to create a verified user account after invitation approval.

    Returns dict {username, temp_password} on success, or None on failure.
    The approval itself is not rolled back on failure — admins can use
    "Create User" to provision the account manually.
    """
    import requests

    from users.models import UserProfile

    authinator_url = getattr(settings, "AUTHINATOR_API_URL", "")
    if not authinator_url:
        logger.info("AUTHINATOR_API_URL not configured, skipping account creation")
        return None

    # Derive a username from the email (part before @)
    base_username = invitation.email.split("@")[0].lower().replace(".", "_")
    service_key = getattr(settings, "SERVICE_REGISTRATION_KEY", "")

    def _try_create(uname):
        """POST to AUTHinator and return (user_data, temp_password) or None."""
        try:
            resp = requests.post(
                f"{authinator_url}create-user/",
                json={"email": invitation.email, "username": uname, "role": "USER"},
                headers={"X-Service-Key": service_key},
                timeout=10,
            )
            if resp.status_code == 201:
                return resp.json()
            logger.warning(
                "AUTHinator create-user returned %s for invitation %s: %s",
                resp.status_code, invitation.id, resp.text,
            )
        except requests.RequestException as exc:
            logger.warning("Failed to reach AUTHinator for invitation %s: %s", invitation.id, exc)
        return None

    user_data = _try_create(base_username)
    if user_data is None:
        # Username might be taken — retry with suffix
        user_data = _try_create(f"{base_username}_{invitation.company_id}")
    if user_data is None:
        return None

    final_username = user_data.get("username", base_username)
    temp_password = user_data.get("temp_password", "")

    # Create matching USERinator profile
    UserProfile.objects.get_or_create(
        user_id=user_data["id"],
        defaults={
            "username": final_username,
            "email": invitation.email,
            "company": invitation.company,
            "display_name": final_username,
            "role_name": invitation.requested_role.role_name,
            "role_level": invitation.requested_role.role_level,
        },
    )
    logger.info(
        "Provisioned user %s (id=%s) via invitation %s",
        final_username, user_data["id"], invitation.id,
    )

    # Send welcome email with credentials
    _send_credentials_email(invitation, final_username, temp_password)

    return {"username": final_username, "temp_password": temp_password}


def _send_credentials_email(invitation, username: str, temp_password: str):
    """Email the new user their login credentials after account creation."""
    from django.core.mail import send_mail

    platform_url = getattr(settings, "FRONTEND_URL", "http://localhost:8080")
    try:
        send_mail(
            subject=f"Welcome to {invitation.company.name} — your account is ready",
            message=(
                f"Hi,\n\n"
                f"Your invitation to join {invitation.company.name} as "
                f"{invitation.requested_role.role_name} has been approved!\n\n"
                f"You can now log in at: {platform_url}\n\n"
                f"Your login details:\n"
                f"  Username: {username}\n"
                f"  Temporary password: {temp_password}\n\n"
                f"Please change your password after your first login.\n\n"
                f"Welcome aboard!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=True,
        )
    except Exception:
        pass
