from django.conf import settings
from django.db import models

from apps.cameras.models import Camera
from apps.common.models import TimestampedModel, UUIDModel
from apps.sites.models import Zone


class EventType(models.TextChoices):
    PERSON_DETECTED = "person_detected", "Person Detected"
    FACE_RECOGNIZED = "face_recognized", "Face Recognized"
    UNKNOWN_PERSON = "unknown_person", "Unknown Person"
    INTRUSION = "intrusion", "Intrusion"
    ACTIVITY = "activity", "Activity"
    ZONE_ENTER = "zone_enter", "Zone Enter"
    ZONE_EXIT = "zone_exit", "Zone Exit"
    LOITERING = "loitering", "Loitering"
    CROWD = "crowd", "Crowd"
    OBJECT_LEFT = "object_left", "Object Left"
    OBJECT_REMOVED = "object_removed", "Object Removed"
    RISK_INCIDENT = "risk_incident", "Risk Incident"
    FIRE = "fire", "Fire"
    SMOKE = "smoke", "Smoke"
    FIRE_SMOKE = "fire_smoke", "Fire/Smoke"
    WEAPON = "weapon", "Weapon"
    FALL = "fall", "Fall"
    FALL_RECOVERY = "fall_recovery", "Fall Recovery"
    PPE_VIOLATION = "ppe_violation", "PPE Violation"
    EMERGENCY_INCIDENT = "emergency_incident", "Emergency Incident"
    ATTENDANCE = "attendance", "Attendance"
    VISITOR = "visitor", "Visitor"


class ReviewStatus(models.TextChoices):
    PENDING = "pending", "Pending Review"
    CONFIRMED = "confirmed", "Confirmed"
    FALSE_POSITIVE = "false_positive", "False Positive"
    ESCALATED = "escalated", "Escalated"


class Severity(models.TextChoices):
    INFO = "info", "Info"
    WARNING = "warning", "Warning"
    CRITICAL = "critical", "Critical"


class DetectionEvent(UUIDModel, TimestampedModel):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="events")
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True, related_name="events")
    edge_device = models.ForeignKey(
        "cameras.EdgeDevice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.INFO)
    confidence = models.FloatField(default=0.0)
    model_name = models.CharField(max_length=128, blank=True)
    model_version = models.CharField(max_length=64, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    review_status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_events",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    retention_until = models.DateTimeField(null=True, blank=True)
    edge_event_id = models.CharField(max_length=128, blank=True, db_index=True)
    # Media references (filled by M6 snapshot upload / recording integrations)
    snapshot_key = models.CharField(max_length=512, blank=True, default="")
    snapshot_url = models.URLField(blank=True, default="")
    evidence_url = models.URLField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["camera", "event_type"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["edge_device", "edge_event_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["edge_device", "edge_event_id"],
                condition=~models.Q(edge_event_id="") & models.Q(edge_device__isnull=False),
                name="events_detectionevent_device_edge_event_uniq",
            ),
            models.UniqueConstraint(
                fields=["camera", "edge_event_id"],
                condition=~models.Q(edge_event_id="") & models.Q(edge_device__isnull=True),
                name="events_detectionevent_camera_edge_event_unbound_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.event_type} @ {self.camera.name}"

    @property
    def organization(self):
        return self.camera.site.organization
