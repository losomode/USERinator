"""Company serializers for USERinator."""

from rest_framework import serializers

from companies.models import Company


class CompanyListSerializer(serializers.ModelSerializer):
    """Summary serializer for list views."""

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "industry",
            "company_size",
            "account_status",
            "logo_url",
        ]
        read_only_fields = fields


class CompanyDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer."""

    class Meta:
        model = Company
        fields = "__all__"
        read_only_fields = ["id", "created_at", "created_by"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        # Hide admin-only notes from non-admins
        if request and getattr(request.user, "role_level", 0) < 30:
            data.pop("notes", None)
            data.pop("billing_contact_email", None)
        return data


class CompanyCreateSerializer(serializers.ModelSerializer):
    """Serializer for company creation (platform admin only)."""

    class Meta:
        model = Company
        fields = [
            "name",
            "address",
            "phone",
            "website",
            "industry",
            "company_size",
            "logo_url",
            "billing_contact_email",
            "custom_fields",
            "tags",
            "notes",
        ]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class CompanyUpdateSerializer(serializers.ModelSerializer):
    """Serializer for company updates (company admin)."""

    class Meta:
        model = Company
        fields = [
            "name",
            "address",
            "phone",
            "website",
            "industry",
            "company_size",
            "logo_url",
            "billing_contact_email",
            "custom_fields",
            "tags",
            "notes",
            "account_status",
        ]
