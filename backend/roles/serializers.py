"""Role serializers for USERinator."""

from rest_framework import serializers

from roles.models import Role


class RoleSerializer(serializers.ModelSerializer):
    """Full role serializer."""

    class Meta:
        model = Role
        fields = "__all__"
        read_only_fields = ["id", "created_at", "created_by"]


class RoleCreateSerializer(serializers.ModelSerializer):
    """Serializer for role creation (platform admin only)."""

    class Meta:
        model = Role
        fields = ["role_name", "role_level", "description"]

    def validate_role_level(self, value):
        if value < 1 or value > 100:
            raise serializers.ValidationError("Role level must be between 1 and 100.")
        return value

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class RoleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for role updates (platform admin, non-system roles only)."""

    class Meta:
        model = Role
        fields = ["role_name", "role_level", "description"]

    def validate_role_level(self, value):
        if value < 1 or value > 100:
            raise serializers.ValidationError("Role level must be between 1 and 100.")
        return value

    def validate(self, data):
        if self.instance and self.instance.is_system_role:
            raise serializers.ValidationError("System roles cannot be modified.")
        return data
