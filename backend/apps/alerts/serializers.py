from rest_framework import serializers

from .models import Alert, AlertRule


class AlertRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertRule
        fields = (
            "id",
            "organization",
            "name",
            "event_type",
            "min_severity",
            "min_confidence",
            "is_active",
            "notify_email",
            "conditions",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class AlertSerializer(serializers.ModelSerializer):
    event_type = serializers.CharField(source="event.event_type", read_only=True)
    camera_name = serializers.CharField(source="event.camera.name", read_only=True)
    site_name = serializers.CharField(source="event.camera.site.name", read_only=True)

    class Meta:
        model = Alert
        fields = (
            "id",
            "organization",
            "event",
            "event_type",
            "camera_name",
            "site_name",
            "rule",
            "title",
            "message",
            "severity",
            "status",
            "acknowledged_by",
            "acknowledged_at",
            "resolved_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "acknowledged_by",
            "acknowledged_at",
            "resolved_at",
            "created_at",
            "updated_at",
        )


class AlertAcknowledgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ("status",)
