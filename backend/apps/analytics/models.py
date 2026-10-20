"""M4 — Advanced security analytics models."""

from django.conf import settings
from django.db import models

from apps.cameras.models import Camera
from apps.common.models import TimestampedModel, UUIDModel
from apps.events.models import DetectionEvent, Severity
from apps.sites.models import Site, Zone
from apps.tenancy.models import Organization


class ZonePriority(models.TextChoices):
    CRITICAL = "critical", "Critical"
    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"


class RiskLevel(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class ObjectEventKind(models.TextChoices):
    LEFT = "left", "Object Left Behind"
    REMOVED = "removed", "Object Removed"


class AnalyticsRule(UUIDModel, TimestampedModel):
    """Configurable detection rule evaluated on ingest (Sprint 6)."""

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="analytics_rules")
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    # Trigger when these event types are seen (any match unless require_all)
    event_types = models.JSONField(default=list, help_text='e.g. ["intrusion","loitering"]')
    require_all = models.BooleanField(
        default=False,
        help_text="If true, all listed event_types must appear in the correlation window",
    )
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True, related_name="analytics_rules")
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True, related_name="analytics_rules")
    # Time window (local site time). Empty = always.
    time_start = models.TimeField(null=True, blank=True)
    time_end = models.TimeField(null=True, blank=True)
    # Correlation
    window_seconds = models.PositiveIntegerField(default=120)
    min_confidence = models.FloatField(default=0.0)
    risk_level = models.CharField(max_length=16, choices=RiskLevel.choices, default=RiskLevel.HIGH)
    conditions = models.JSONField(default=dict, blank=True)
    priority = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ["priority", "name"]
        unique_together = ("organization", "name")

    def __str__(self):
        return self.name


class RuleAction(UUIDModel, TimestampedModel):
    rule = models.ForeignKey(AnalyticsRule, on_delete=models.CASCADE, related_name="actions")
    action_type = models.CharField(
        max_length=32,
        choices=[
            ("alert", "Create Alert"),
            ("snapshot", "Save Snapshot"),
            ("recording", "Start Recording"),
            ("notify", "Notify"),
        ],
    )
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["action_type"]


class LoiterEvent(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="loiter_events")
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="loiter_events")
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True, related_name="loiter_events")
    detection_event = models.ForeignKey(
        DetectionEvent, on_delete=models.SET_NULL, null=True, blank=True, related_name="loiter_events"
    )
    track_id = models.IntegerField(null=True, blank=True)
    dwell_seconds = models.FloatField(default=0.0)
    threshold_seconds = models.FloatField(default=0.0)
    person_type = models.CharField(max_length=32, blank=True, default="")
    escalation_count = models.PositiveIntegerField(default=1)
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.WARNING)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["organization", "-created_at"])]


class CrowdStatistic(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="crowd_stats")
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="crowd_stats")
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True, related_name="crowd_stats")
    occupancy = models.PositiveIntegerField(default=0)
    max_occupancy = models.PositiveIntegerField(null=True, blank=True)
    density = models.FloatField(default=0.0, help_text="people per normalized zone area unit")
    over_capacity = models.BooleanField(default=False)
    peak_hour = models.PositiveSmallIntegerField(null=True, blank=True)
    heatmap = models.JSONField(default=list, blank=True, help_text="List of {x,y,w} cells")
    recorded_at = models.DateTimeField()

    class Meta:
        ordering = ["-recorded_at"]
        indexes = [models.Index(fields=["organization", "camera", "-recorded_at"])]


class ObjectEvent(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="object_events")
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="object_events")
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True, related_name="object_events")
    detection_event = models.ForeignKey(
        DetectionEvent, on_delete=models.SET_NULL, null=True, blank=True, related_name="object_events"
    )
    kind = models.CharField(max_length=16, choices=ObjectEventKind.choices)
    object_class = models.CharField(max_length=64, default="bag")
    track_id = models.IntegerField(null=True, blank=True)
    confidence = models.FloatField(default=0.0)
    dwell_seconds = models.FloatField(default=0.0)
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.WARNING)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["organization", "kind", "-created_at"])]


class RiskIncident(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="risk_incidents")
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True, related_name="risk_incidents")
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True, related_name="risk_incidents")
    camera = models.ForeignKey(Camera, on_delete=models.SET_NULL, null=True, blank=True, related_name="risk_incidents")
    rule = models.ForeignKey(AnalyticsRule, on_delete=models.SET_NULL, null=True, blank=True, related_name="incidents")
    title = models.CharField(max_length=255)
    risk_level = models.CharField(max_length=16, choices=RiskLevel.choices, default=RiskLevel.MEDIUM)
    risk_score = models.FloatField(default=0.0)
    status = models.CharField(
        max_length=20,
        choices=[
            ("open", "Open"),
            ("acknowledged", "Acknowledged"),
            ("resolved", "Resolved"),
            ("false_positive", "False Positive"),
        ],
        default="open",
    )
    summary = models.TextField(blank=True, default="")
    actions_taken = models.JSONField(default=list, blank=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="acked_incidents"
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["organization", "risk_level", "-created_at"])]


class EventCorrelation(UUIDModel, TimestampedModel):
    incident = models.ForeignKey(RiskIncident, on_delete=models.CASCADE, related_name="correlations")
    event = models.ForeignKey(DetectionEvent, on_delete=models.CASCADE, related_name="correlations")
    weight = models.FloatField(default=1.0)

    class Meta:
        unique_together = ("incident", "event")
        ordering = ["-created_at"]
