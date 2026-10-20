from rest_framework import serializers

from .models import Organization, Role, UserMembership


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "slug", "settings", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class UserMembershipSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserMembership
        fields = ("id", "organization", "role", "username", "email", "created_at")
        read_only_fields = fields


class MembershipMeSerializer(serializers.Serializer):
    organization = OrganizationSerializer()
    role = serializers.ChoiceField(choices=Role.choices)
