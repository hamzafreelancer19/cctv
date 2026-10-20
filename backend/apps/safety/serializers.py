from rest_framework import serializers

from .models import (
    EmergencyAction,
    EmergencyEscalation,
    EmergencyIncident,
    FallEvent,
    FireEvent,
    PPEEvent,
    SafetyProfile,
    SmokeEvent,
    WeaponEvent,
)


class SafetyEventSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source="camera.name", read_only=True)
    site_name = serializers.CharField(source="camera.site.name", read_only=True)
    zone_name = serializers.CharField(source="zone.name", read_only=True, allow_null=True)


class FireEventSerializer(SafetyEventSerializer):
    class Meta:
        model = FireEvent
        fields = "__all__"


class SmokeEventSerializer(SafetyEventSerializer):
    class Meta:
        model = SmokeEvent
        fields = "__all__"


class WeaponEventSerializer(SafetyEventSerializer):
    person_name = serializers.CharField(source="person.full_name", read_only=True, allow_null=True)

    class Meta:
        model = WeaponEvent
        fields = "__all__"


class FallEventSerializer(SafetyEventSerializer):
    person_name = serializers.CharField(source="person.full_name", read_only=True, allow_null=True)

    class Meta:
        model = FallEvent
        fields = "__all__"


class PPEEventSerializer(SafetyEventSerializer):
    person_name = serializers.CharField(source="person.full_name", read_only=True, allow_null=True)

    class Meta:
        model = PPEEvent
        fields = "__all__"


class SafetyProfileSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source="camera.name", read_only=True)

    class Meta:
        model = SafetyProfile
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class EmergencyActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyAction
        fields = ("id", "action_type", "status", "details", "executed_at", "created_at")


class EmergencyEscalationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyEscalation
        fields = ("id", "from_severity", "to_severity", "reason", "created_at")


class EmergencyIncidentSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source="site.name", read_only=True, allow_null=True)
    camera_name = serializers.CharField(source="camera.name", read_only=True, allow_null=True)
    zone_name = serializers.CharField(source="zone.name", read_only=True, allow_null=True)
    event_count = serializers.IntegerField(source="event_links.count", read_only=True)
    actions = EmergencyActionSerializer(many=True, read_only=True)
    escalations = EmergencyEscalationSerializer(many=True, read_only=True)

    class Meta:
        model = EmergencyIncident
        fields = "__all__"
