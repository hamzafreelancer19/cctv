from rest_framework import serializers

from apps.cameras.models import Camera
from apps.sites.models import Zone

from .models import (
    AnalyticsRule,
    CrowdStatistic,
    LoiterEvent,
    ObjectEvent,
    RiskIncident,
    RuleAction,
)


class ZoneAnalyticsSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source="site.name", read_only=True)
    organization = serializers.UUIDField(source="site.organization_id", read_only=True)
    camera_ids = serializers.PrimaryKeyRelatedField(
        source="linked_cameras", many=True, queryset=Camera.objects.all(), required=False
    )

    class Meta:
        model = Zone
        fields = (
            "id",
            "site",
            "site_name",
            "organization",
            "name",
            "polygon_json",
            "is_restricted",
            "is_active",
            "priority",
            "loitering_seconds",
            "visitor_loitering_seconds",
            "ignore_employees",
            "max_occupancy",
            "access_start",
            "access_end",
            "after_hours_restricted",
            "entry_line_json",
            "camera_ids",
            "config_version",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "config_version", "created_at", "updated_at")


class RuleActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleAction
        fields = ("id", "action_type", "config", "is_active")


class AnalyticsRuleSerializer(serializers.ModelSerializer):
    actions = RuleActionSerializer(many=True, required=False)
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = AnalyticsRule
        fields = (
            "id",
            "organization",
            "organization_name",
            "name",
            "description",
            "is_active",
            "event_types",
            "require_all",
            "zone",
            "site",
            "time_start",
            "time_end",
            "window_seconds",
            "min_confidence",
            "risk_level",
            "conditions",
            "priority",
            "actions",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def create(self, validated_data):
        actions_data = validated_data.pop("actions", [])
        rule = AnalyticsRule.objects.create(**validated_data)
        for action in actions_data:
            RuleAction.objects.create(rule=rule, **action)
        return rule


class LoiterEventSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source="camera.name", read_only=True)
    zone_name = serializers.CharField(source="zone.name", read_only=True, allow_null=True)

    class Meta:
        model = LoiterEvent
        fields = (
            "id",
            "camera",
            "camera_name",
            "zone",
            "zone_name",
            "track_id",
            "dwell_seconds",
            "threshold_seconds",
            "person_type",
            "escalation_count",
            "severity",
            "payload",
            "created_at",
        )


class CrowdStatisticSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source="camera.name", read_only=True)
    zone_name = serializers.CharField(source="zone.name", read_only=True, allow_null=True)

    class Meta:
        model = CrowdStatistic
        fields = (
            "id",
            "camera",
            "camera_name",
            "zone",
            "zone_name",
            "occupancy",
            "max_occupancy",
            "density",
            "over_capacity",
            "peak_hour",
            "heatmap",
            "recorded_at",
            "created_at",
        )


class ObjectEventSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source="camera.name", read_only=True)
    zone_name = serializers.CharField(source="zone.name", read_only=True, allow_null=True)

    class Meta:
        model = ObjectEvent
        fields = (
            "id",
            "camera",
            "camera_name",
            "zone",
            "zone_name",
            "kind",
            "object_class",
            "track_id",
            "confidence",
            "dwell_seconds",
            "severity",
            "payload",
            "created_at",
        )


class RiskIncidentSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source="camera.name", read_only=True, allow_null=True)
    site_name = serializers.CharField(source="site.name", read_only=True, allow_null=True)
    zone_name = serializers.CharField(source="zone.name", read_only=True, allow_null=True)
    rule_name = serializers.CharField(source="rule.name", read_only=True, allow_null=True)
    event_count = serializers.SerializerMethodField()

    class Meta:
        model = RiskIncident
        fields = (
            "id",
            "title",
            "risk_level",
            "risk_score",
            "status",
            "summary",
            "actions_taken",
            "camera",
            "camera_name",
            "site",
            "site_name",
            "zone",
            "zone_name",
            "rule",
            "rule_name",
            "event_count",
            "created_at",
            "acknowledged_at",
            "resolved_at",
        )

    def get_event_count(self, obj):
        return obj.correlations.count()
