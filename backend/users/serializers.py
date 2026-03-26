"""User profile serializers for USERinator."""

from rest_framework import serializers

from users.models import UserProfile


class UserProfileListSerializer(serializers.ModelSerializer):
    """Summary serializer for list views."""

    company_name = serializers.CharField(
        source="company.name", read_only=True, allow_null=True, default=None
    )

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
            "company_name",
            "is_active",
            "marked_for_deletion",
            "marked_for_deletion_at",
        ]
        read_only_fields = fields


class UserProfileDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer."""

    company_name = serializers.CharField(
        source="company.name", read_only=True, allow_null=True, default=None
    )

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
    """Serializer for admin updates (includes role + company fields)."""

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
            "company",
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

    def validate(self, attrs):
        """Enforce platform/company consistency when role or company changes."""
        from core.permissions import PLATFORM_ROLE_THRESHOLD

        # Only validate if both fields are being updated
        role_level = attrs.get("role_level")
        company = attrs.get("company")

        if role_level is not None and company is not None:
            if role_level >= PLATFORM_ROLE_THRESHOLD and company:
                raise serializers.ValidationError(
                    {"company": "Platform-level roles (level \u2265 60) cannot be associated with a company."}
                )
            if role_level < PLATFORM_ROLE_THRESHOLD and not company:
                raise serializers.ValidationError(
                    {"company": "Company-level roles (level < 60) require a company."}
                )
        return attrs


class UserProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for admin-only profile creation."""

    # company is optional — required for company roles (< 60), forbidden for platform roles (>= 60)
    company = serializers.PrimaryKeyRelatedField(
        queryset=__import__("companies.models", fromlist=["Company"]).Company.objects.all(),
        required=False,
        allow_null=True,
    )

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
        """Cannot assign a role higher than your own."""
        request = self.context.get("request")
        if request:
            user_role_level = getattr(request.user, "role_level", 0)
            if value > user_role_level:
                raise serializers.ValidationError(
                    "Cannot assign a role level higher than your own."
                )
        return value

    def validate(self, attrs):
        """Cross-field validation: enforce platform/company role rules."""
        from core.permissions import PLATFORM_ROLE_THRESHOLD

        role_level = attrs.get("role_level", 10)
        company = attrs.get("company")
        request = self.context.get("request")

        # Platform roles must NOT have a company
        if role_level >= PLATFORM_ROLE_THRESHOLD and company is not None:
            raise serializers.ValidationError(
                {"company": "Platform-level roles (level \u2265 60) cannot be associated with a company."}
            )

        # Company roles MUST have a company
        if role_level < PLATFORM_ROLE_THRESHOLD and company is None:
            raise serializers.ValidationError(
                {"company": "Company-level roles (level < 60) require a company assignment."}
            )

        # MANAGER can only create users for their own company
        if request and company is not None:
            user_role_level = getattr(request.user, "role_level", 0)
            user_company = getattr(request.user, "company_id_remote", None)
            if user_role_level < 100 and company.id != user_company:
                raise serializers.ValidationError(
                    {"company": "You can only create users for your own company."}
                )

        return attrs

    def create(self, validated_data):
        """Create or reactivate a UserProfile.

        If a soft-deleted profile exists for the given user_id, reactivate it
        rather than failing with a unique-constraint error.
        """
        try:
            existing = UserProfile.objects.get(user_id=validated_data["user_id"])
            # Reactivate and update fields
            for field, value in validated_data.items():
                setattr(existing, field, value)
            existing.is_active = True
            existing.save()
            return existing
        except UserProfile.DoesNotExist:
            return super().create(validated_data)


class UserRoleSerializer(serializers.ModelSerializer):
    """Minimal serializer for AUTHinator role queries."""

    class Meta:
        model = UserProfile
        fields = ["user_id", "role_name", "role_level", "company"]


class UserContextSerializer(serializers.ModelSerializer):
    """Complete user context for service authorization.
    
    Returns all data needed for authorization decisions:
    - company_id, company_name for company-scoped queries
    - role_name, role_level for permission checks
    - username, email for audit logging
    """
    company_id = serializers.IntegerField(source='company.id', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user_id",
            "username",
            "email",
            "company_id",
            "company_name",
            "role_name",
            "role_level",
            "is_active",
        ]


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
