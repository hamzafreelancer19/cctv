from rest_framework import serializers

from .models import DetectionEvent, EventType, ReviewStatus, Severity


class DetectionEventSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source="camera.name", read_only=True)
    site_name = serializers.CharField(source="camera.site.name", read_only=True)
    organization = serializers.UUIDField(source="camera.site.organization_id", read_only=True)
    edge_device_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = DetectionEvent
        fields = (
            "id",
            "camera",
            "camera_name",
            "site_name",
            "organization",
            "zone",
            "edge_device_id",
            "event_type",
            "severity",
            "confidence",
            "model_name",
            "model_version",
            "payload",
            "review_status",
            "reviewed_by",
            "reviewed_at",
            "edge_event_id",
            "snapshot_key",
            "snapshot_url",
            "evidence_url",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "reviewed_by",
            "reviewed_at",
            "snapshot_key",
            "snapshot_url",
            "evidence_url",
            "created_at",
            "updated_at",
        )


class EventIngestSerializer(serializers.Serializer):
    camera_id = serializers.UUIDField()
    event_type = serializers.ChoiceField(choices=EventType.choices)
    severity = serializers.ChoiceField(choices=Severity.choices, default=Severity.INFO)
    confidence = serializers.FloatField(min_value=0.0, max_value=1.0, default=0.0)
    model_name = serializers.CharField(max_length=128, required=False, allow_blank=True)
    model_version = serializers.CharField(max_length=64, required=False, allow_blank=True)
    payload = serializers.JSONField(required=False, default=dict)
    zone_id = serializers.UUIDField(required=False, allow_null=True)
    zone_version = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    edge_event_id = serializers.CharField(max_length=128, required=False, allow_blank=True)


class EventReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectionEvent
        fields = ("review_status",)
        extra_kwargs = {"review_status": {"choices": ReviewStatus.choices}}
