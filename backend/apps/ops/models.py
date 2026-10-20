"""M6 enterprise operations: notifications, evidence, recording, SSO, SIEM."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.cameras.models import Camera
from apps.common.models import TimestampedModel, UUIDModel
from apps.events.models import DetectionEvent
from apps.tenancy.models import Organization


class NotificationChannel(models.TextChoices):
    EMAIL = "email", "Email"
    SMS = "sms", "SMS"
    WHATSAPP = "whatsapp", "WhatsApp"
    PUSH = "push", "Push"
    WEBHOOK = "webhook", "Webhook"


class NotificationStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    SENDING = "sending", "Sending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    DEAD = "dead", "Dead Letter"


class NotificationJob(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="notification_jobs")
    event = models.ForeignKey(
        DetectionEvent, on_delete=models.SET_NULL, null=True, blank=True, related_name="notification_jobs"
    )
    channel = models.CharField(max_length=16, choices=NotificationChannel.choices)
    destination = models.CharField(max_length=512, blank=True, default="")
    subject = models.CharField(max_length=255, blank=True, default="")
    body = models.TextField(blank=True, default="")
    status = models.CharField(max_length=16, choices=NotificationStatus.choices, default=NotificationStatus.QUEUED)
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=5)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    last_error = models.TextField(blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)
    rate_limit_key = models.CharField(max_length=128, blank=True, default="")
    celery_task_id = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "next_attempt_at"])]


class NotificationDeliveryLog(UUIDModel, TimestampedModel):
    job = models.ForeignKey(NotificationJob, on_delete=models.CASCADE, related_name="delivery_logs")
    attempt = models.PositiveIntegerField(default=1)
    success = models.BooleanField(default=False)
    provider_response = models.TextField(blank=True, default="")
    latency_ms = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]


class SnapshotObject(UUIDModel, TimestampedModel):
    """Backend-accessible snapshot metadata (S3/MinIO or local media)."""

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="snapshots")
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="snapshots")
    event = models.ForeignKey(
        DetectionEvent, on_delete=models.SET_NULL, null=True, blank=True, related_name="snapshots"
    )
    snapshot_key = models.CharField(max_length=512)
    snapshot_url = models.URLField(blank=True, default="")
    thumbnail_url = models.URLField(blank=True, default="")
    content_type = models.CharField(max_length=64, default="image/jpeg")
    mime_type = models.CharField(max_length=64, blank=True, default="")
    checksum = models.CharField(max_length=128, blank=True, default="")
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    size_bytes = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    uploaded_by_edge = models.BooleanField(default=True)
    storage_backend = models.CharField(max_length=16, default="local")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["organization", "-created_at"])]


class RecordingVendor(models.TextChoices):
    ONVIF = "onvif", "ONVIF"
    MILESTONE = "milestone", "Milestone"
    HIKVISION = "hikvision", "Hikvision"
    DAHUA = "dahua", "Dahua"
    AXIS = "axis", "Axis"
    RTSP = "rtsp", "Generic RTSP"
    STUB = "stub", "Stub"


class RecordingStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    RECORDING = "recording", "Recording"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"


class RecordingJob(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="recording_jobs")
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="recording_jobs")
    event = models.ForeignKey(
        DetectionEvent, on_delete=models.SET_NULL, null=True, blank=True, related_name="recording_jobs"
    )
    vendor = models.CharField(max_length=20, choices=RecordingVendor.choices, default=RecordingVendor.STUB)
    status = models.CharField(max_length=16, choices=RecordingStatus.choices, default=RecordingStatus.REQUESTED)
    evidence_url = models.URLField(blank=True, default="")
    clip_key = models.CharField(max_length=512, blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]


class SSOProtocol(models.TextChoices):
    OIDC = "oidc", "OpenID Connect"
    SAML = "saml", "SAML 2.0"
    LDAP = "ldap", "LDAP / Active Directory"


class SSOProvider(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="sso_providers")
    name = models.CharField(max_length=128)
    protocol = models.CharField(max_length=16, choices=SSOProtocol.choices, default=SSOProtocol.OIDC)
    issuer = models.CharField(max_length=512, blank=True, default="")
    client_id = models.CharField(max_length=255, blank=True, default="")
    client_secret = models.CharField(max_length=512, blank=True, default="")
    metadata_url = models.URLField(blank=True, default="")
    authorization_url = models.URLField(blank=True, default="")
    token_url = models.URLField(blank=True, default="")
    jwks_url = models.URLField(blank=True, default="")
    scim_enabled = models.BooleanField(default=False)
    mfa_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("organization", "name")
        ordering = ["name"]


class SIEMTarget(models.TextChoices):
    SPLUNK = "splunk", "Splunk"
    SENTINEL = "sentinel", "Microsoft Sentinel"
    QRADAR = "qradar", "IBM QRadar"
    ELASTIC = "elastic", "Elastic Security"
    SYSLOG = "syslog", "Generic Syslog"
    WEBHOOK = "webhook", "Generic Webhook"


class SIEMForwardJob(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="siem_jobs")
    event = models.ForeignKey(
        DetectionEvent, on_delete=models.SET_NULL, null=True, blank=True, related_name="siem_jobs"
    )
    target = models.CharField(max_length=20, choices=SIEMTarget.choices, default=SIEMTarget.WEBHOOK)
    destination = models.CharField(max_length=512)
    status = models.CharField(max_length=16, choices=NotificationStatus.choices, default=NotificationStatus.QUEUED)
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=5)
    last_error = models.TextField(blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]


class PasswordPolicy(UUIDModel, TimestampedModel):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name="password_policy")
    min_length = models.PositiveIntegerField(default=12)
    require_uppercase = models.BooleanField(default=True)
    require_lowercase = models.BooleanField(default=True)
    require_digit = models.BooleanField(default=True)
    require_special = models.BooleanField(default=True)
    password_history = models.PositiveIntegerField(default=5)
    max_age_days = models.PositiveIntegerField(default=90)
    lockout_threshold = models.PositiveIntegerField(default=5)


class SessionPolicy(UUIDModel, TimestampedModel):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name="session_policy")
    idle_timeout_minutes = models.PositiveIntegerField(default=30)
    absolute_timeout_hours = models.PositiveIntegerField(default=12)
    single_session = models.BooleanField(default=False)
    mfa_required = models.BooleanField(default=False)
    remember_me_days = models.PositiveIntegerField(default=0)
