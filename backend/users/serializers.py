"""User profile serializers for USERinator."""

from rest_framework import serializers

from users.models import UserProfile


class UserProfileListSerializer(serializers.ModelSerializer):
    """Summary serializer for list views."""

    class Meta:
        model = UserProfile
        fields = [
            "user_id",
            "username",
            "email",
            "display_name",
            "job_title",
            "department",
            "role_name",
            "role_level",
            "avatar_url",
            "company",
        ]
        read_only_fields = fields


class UserProfileDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer."""

    class Meta:
        model = UserProfile
        fields = "__all__"
        read_only_fields = [
            "user_id",
            "username",
            "created_at",
            "updated_at",
            "last_synced_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        # Hide admin-only notes from non-admins
        if request and getattr(request.user, "role_level", 0) < 30:
            data.pop("notification_email", None)
            data.pop("notification_in_app", None)
        return data


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for self-update (limited fields)."""

    class Meta:
        model = UserProfile
        fields = [
            "display_name",
            "avatar_url",
            "phone",
            "bio",
            "job_title",
            "department",
            "location",
            "timezone",
            "language",
            "notification_email",
            "notification_in_app",
        ]


class UserProfileAdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin updates (includes role fields)."""

    class Meta:
        model = UserProfile
        fields = [
            "display_name",
            "avatar_url",
            "phone",
            "bio",
            "job_title",
            "department",
            "location",
            "role_name",
            "role_level",
            "timezone",
            "language",
            "notification_email",
            "notification_in_app",
            "is_active",
        ]

    def validate_role_level(self, value):
        """Prevent privilege escalation."""
        request = self.context.get("request")
        if request:
            user_role_level = getattr(request.user, "role_level", 0)
            if value > user_role_level:
                raise serializers.ValidationError(
                    "Cannot assign a role level higher than your own."
                )
        return value


class UserProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for admin-only profile creation."""

    class Meta:
        model = UserProfile
        fields = [
            "user_id",
            "username",
            "email",
            "company",
            "display_name",
            "role_name",
            "role_level",
        ]

    def validate_role_level(self, value):
        request = self.context.get("request")
        if request:
            user_role_level = getattr(request.user, "role_level", 0)
            if value > user_role_level:
                raise serializers.ValidationError(
                    "Cannot assign a role level higher than your own."
                )
        return value


class UserRoleSerializer(serializers.ModelSerializer):
    """Minimal serializer for AUTHinator role queries."""

    class Meta:
        model = UserProfile
        fields = ["user_id", "role_name", "role_level", "company"]


class PreferencesSerializer(serializers.ModelSerializer):
    """Serializer for user preferences (subset of UserProfile)."""

    class Meta:
        model = UserProfile
        fields = [
            "timezone",
            "language",
            "notification_email",
            "notification_in_app",
        ]

    def validate_timezone(self, value):
        """Validate timezone string."""
        import zoneinfo

        try:
            zoneinfo.ZoneInfo(value)
        except (KeyError, Exception):
            raise serializers.ValidationError(f"Invalid timezone: {value}")
        return value

    def validate_language(self, value):
        """Validate language code."""
        supported = ["en", "es", "fr", "de", "pt", "zh", "ja", "ko"]
        if value not in supported:
            raise serializers.ValidationError(
                f'Unsupported language: {value}. Supported: {", ".join(supported)}'
            )
        return value
