from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True, allow_null=True)

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "organization",
            "actor",
            "actor_username",
            "action",
            "resource_type",
            "resource_id",
            "ip_address",
            "details",
            "created_at",
        )
        read_only_fields = fields
