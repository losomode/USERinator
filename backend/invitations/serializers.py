"""Invitation serializers for USERinator."""

from rest_framework import serializers

from invitations.models import UserInvitation


class InvitationSerializer(serializers.ModelSerializer):
    """Full invitation serializer."""

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

    def validate(self, data):
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
