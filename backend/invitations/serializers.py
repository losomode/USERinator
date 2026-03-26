"""Invitation serializers for USERinator."""

from rest_framework import serializers

from invitations.models import UserInvitation


class InvitationSerializer(serializers.ModelSerializer):
    """Full invitation serializer."""

    requested_role_name = serializers.CharField(source="requested_role.role_name", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = UserInvitation
        fields = "__all__"
        read_only_fields = [
            "id",
            "requested_at",
            "reviewed_at",
            "reviewed_by",
            "review_notes",
            "expires_at",
        ]


class InvitationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an invitation request."""

    class Meta:
        model = UserInvitation
        fields = ["email", "company", "requested_role", "message"]

    def validate_requested_role(self, role):
        """Invitations are only for company-level roles (level < 60)."""
        from core.permissions import PLATFORM_ROLE_THRESHOLD
        if role.role_level >= PLATFORM_ROLE_THRESHOLD:
            raise serializers.ValidationError(
                "Platform-level roles cannot be assigned via invitation. "
                "Use the Create User function instead."
            )
        return role

    def validate(self, data):
        from core.permissions import PLATFORM_ROLE_THRESHOLD

        # Enforce requesting user cannot assign a role higher than their own
        request = self.context.get("request")
        if request:
            user_role_level = getattr(request.user, "role_level", 0)
            invited_level = data["requested_role"].role_level
            if invited_level > user_role_level:
                raise serializers.ValidationError(
                    {"requested_role": "You cannot invite users to a role higher than your own."}
                )

        # Check for duplicate pending invitation
        existing = UserInvitation.objects.filter(
            email=data["email"],
            company=data["company"],
            status=UserInvitation.Status.PENDING,
        ).exists()
        if existing:
            raise serializers.ValidationError(
                "A pending invitation already exists for this email and company."
            )
        return data


class InvitationReviewSerializer(serializers.Serializer):
    """Serializer for approving/rejecting invitations."""

    review_notes = serializers.CharField(required=False, allow_blank=True)
