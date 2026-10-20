from rest_framework import serializers

from .models import (
    NotificationDeliveryLog,
    NotificationJob,
    PasswordPolicy,
    RecordingJob,
    SessionPolicy,
    SIEMForwardJob,
    SnapshotObject,
    SSOProvider,
)


class NotificationJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationJob
        fields = (
            "id",
            "channel",
            "destination",
            "subject",
            "status",
            "attempts",
            "max_attempts",
            "next_attempt_at",
            "last_error",
            "event",
            "rate_limit_key",
            "celery_task_id",
            "created_at",
        )


class NotificationDeliveryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationDeliveryLog
        fields = (
            "id",
            "job",
            "attempt",
            "success",
            "provider_response",
            "latency_ms",
            "error",
            "created_at",
        )


class RecordingJobSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source="camera.name", read_only=True)

    class Meta:
        model = RecordingJob
        fields = (
            "id",
            "camera",
            "camera_name",
            "event",
            "vendor",
            "status",
            "evidence_url",
            "clip_key",
            "started_at",
            "ended_at",
            "details",
            "created_at",
        )


class SnapshotObjectSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source="camera.name", read_only=True)

    class Meta:
        model = SnapshotObject
        fields = (
            "id",
            "camera",
            "camera_name",
            "event",
            "snapshot_key",
            "snapshot_url",
            "thumbnail_url",
            "content_type",
            "mime_type",
            "checksum",
            "width",
            "height",
            "size_bytes",
            "expires_at",
            "uploaded_by_edge",
            "storage_backend",
            "created_at",
        )


class SSOProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SSOProvider
        fields = (
            "id",
            "organization",
            "name",
            "protocol",
            "issuer",
            "client_id",
            "client_secret",
            "metadata_url",
            "authorization_url",
            "token_url",
            "jwks_url",
            "scim_enabled",
            "mfa_required",
            "is_active",
            "settings",
            "created_at",
        )
        extra_kwargs = {"client_secret": {"write_only": True}}
        read_only_fields = ("id", "created_at")



class PasswordPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordPolicy
        fields = (
            "id",
            "organization",
            "min_length",
            "require_uppercase",
            "require_lowercase",
            "require_digit",
            "require_special",
            "password_history",
            "max_age_days",
            "lockout_threshold",
        )
        read_only_fields = ("id", "organization")


class SessionPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionPolicy
        fields = (
            "id",
            "organization",
            "idle_timeout_minutes",
            "absolute_timeout_hours",
            "single_session",
            "mfa_required",
            "remember_me_days",
        )
        read_only_fields = ("id", "organization")


class SIEMForwardJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = SIEMForwardJob
        fields = (
            "id",
            "event",
            "target",
            "destination",
            "status",
            "attempts",
            "max_attempts",
            "last_error",
            "created_at",
        )
