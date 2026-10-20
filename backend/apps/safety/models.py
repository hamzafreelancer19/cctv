"""M5 life-safety event and emergency incident models."""

from django.conf import settings
from django.db import models

from apps.cameras.models import Camera
from apps.common.models import TimestampedModel, UUIDModel
from apps.events.models import DetectionEvent
from apps.identity.models import Person
from apps.sites.models import Zone
from apps.tenancy.models import Organization


def default_required_ppe():
    return ["helmet", "safety_vest"]


class EmergencySeverity(models.TextChoices):
    WARNING = "warning", "Warning"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"
    EMERGENCY = "emergency", "Emergency"


class EmergencyStatus(models.TextChoices):
    OPEN = "open", "Open"
    ACKNOWLEDGED = "acknowledged", "Acknowledged"
    CONTAINED = "contained", "Contained"
    RESOLVED = "resolved", "Resolved"
    FALSE_POSITIVE = "false_positive", "False Positive"


class SafetyProfile(UUIDModel, TimestampedModel):
    """Camera-specific detector sensitivity and temporal confirmation."""

    camera = models.OneToOneField(Camera, on_delete=models.CASCADE, related_name="safety_profile")
    environment = models.CharField(
        max_length=16,
        choices=[("indoor", "Indoor"), ("outdoor", "Outdoor")],
        default="indoor",
    )
    fire_threshold = models.FloatField(default=0.75)
    fire_confirmation_frames = models.PositiveSmallIntegerField(default=3)
    smoke_threshold = models.FloatField(default=0.55)
    smoke_persistence_seconds = models.FloatField(default=8.0)
    smoke_sensitivity = models.FloatField(default=1.0)
    weapon_threshold = models.FloatField(default=0.65)
    detect_knives = models.BooleanField(default=False)
    fall_confirmation_seconds = models.FloatField(default=2.0)
    fall_immobility_seconds = models.FloatField(default=20.0)
    ppe_required = models.JSONField(default=default_required_ppe)
    ppe_model_enabled = models.BooleanField(default=False)
    ppe_contractor_only = models.BooleanField(default=False)
    ppe_shift_start = models.TimeField(null=True, blank=True)
    ppe_shift_end = models.TimeField(null=True, blank=True)
    ppe_zones = models.ManyToManyField(Zone, blank=True, related_name="ppe_profiles")
    is_active = models.BooleanField(default=True)


class SafetyEventBase(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True)
    detection_event = models.OneToOneField(DetectionEvent, on_delete=models.CASCADE)
    confidence = models.FloatField(default=0.0)
    duration_seconds = models.FloatField(default=0.0)
    snapshot_path = models.CharField(max_length=512, blank=True, default="")
    evidence_clip_path = models.CharField(max_length=512, blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class FireEvent(SafetyEventBase):
    environment = models.CharField(max_length=16, default="indoor")
    confirmation_frames = models.PositiveSmallIntegerField(default=1)
    flame_area_ratio = models.FloatField(default=0.0)
    verified = models.BooleanField(default=False)


class SmokeEvent(SafetyEventBase):
    density = models.FloatField(default=0.0)
    density_level = models.CharField(max_length=16, default="low")
    trend = models.CharField(max_length=16, default="stable")
    persistent = models.BooleanField(default=False)


class WeaponEvent(SafetyEventBase):
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    track_id = models.IntegerField(null=True, blank=True)
    weapon_type = models.CharField(max_length=32)
    associated = models.BooleanField(default=False)


class FallEvent(SafetyEventBase):
    track_id = models.IntegerField(null=True, blank=True)
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=[("fallen", "Fallen"), ("immobile", "Immobile"), ("recovered", "Recovered")],
        default="fallen",
    )
    immobile_seconds = models.FloatField(default=0.0)
    recovered_at = models.DateTimeField(null=True, blank=True)


class PPEEvent(SafetyEventBase):
    track_id = models.IntegerField(null=True, blank=True)
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    person_type = models.CharField(max_length=32, blank=True, default="")
    required_items = models.JSONField(default=list)
    missing_items = models.JSONField(default=list)
    compliant = models.BooleanField(default=False)


class EmergencyIncident(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="emergency_incidents")
    site = models.ForeignKey("sites.Site", on_delete=models.SET_NULL, null=True, blank=True)
    camera = models.ForeignKey(Camera, on_delete=models.SET_NULL, null=True, blank=True)
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    severity = models.CharField(
        max_length=16, choices=EmergencySeverity.choices, default=EmergencySeverity.WARNING
    )
    status = models.CharField(max_length=20, choices=EmergencyStatus.choices, default=EmergencyStatus.OPEN)
    score = models.FloatField(default=0.0)
    summary = models.TextField(blank=True, default="")
    recommended_actions = models.JSONField(default=list, blank=True)
    continuous_recording_requested = models.BooleanField(default=False)
    notifications_requested = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acknowledged_emergencies",
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["organization", "status", "-created_at"])]


class EmergencyEventLink(UUIDModel, TimestampedModel):
    incident = models.ForeignKey(EmergencyIncident, on_delete=models.CASCADE, related_name="event_links")
    event = models.ForeignKey(DetectionEvent, on_delete=models.CASCADE, related_name="emergency_links")

    class Meta:
        unique_together = ("incident", "event")


class EmergencyAction(UUIDModel, TimestampedModel):
    incident = models.ForeignKey(EmergencyIncident, on_delete=models.CASCADE, related_name="actions")
    action_type = models.CharField(max_length=32)
    status = models.CharField(max_length=20, default="requested")
    details = models.JSONField(default=dict, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)


class EmergencyEscalation(UUIDModel, TimestampedModel):
    incident = models.ForeignKey(EmergencyIncident, on_delete=models.CASCADE, related_name="escalations")
    from_severity = models.CharField(max_length=16, choices=EmergencySeverity.choices)
    to_severity = models.CharField(max_length=16, choices=EmergencySeverity.choices)
    reason = models.TextField()
