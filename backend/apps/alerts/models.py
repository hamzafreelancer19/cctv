from django.conf import settings
from django.db import models

from apps.common.models import TimestampedModel, UUIDModel
from apps.events.models import DetectionEvent, EventType, Severity
from apps.tenancy.models import Organization


class AlertStatus(models.TextChoices):
    OPEN = "open", "Open"
    ACKNOWLEDGED = "acknowledged", "Acknowledged"
    RESOLVED = "resolved", "Resolved"
    DISMISSED = "dismissed", "Dismissed"


class AlertRule(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="alert_rules")
    name = models.CharField(max_length=255)
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    min_severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.WARNING)
    min_confidence = models.FloatField(default=0.5)
    is_active = models.BooleanField(default=True)
    notify_email = models.BooleanField(default=True)
    conditions = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class Alert(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="alerts")
    event = models.ForeignKey(DetectionEvent, on_delete=models.CASCADE, related_name="alerts")
    rule = models.ForeignKey(AlertRule, on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts")
    title = models.CharField(max_length=512)
    message = models.TextField(blank=True)
    severity = models.CharField(max_length=16, choices=Severity.choices)
    status = models.CharField(max_length=20, choices=AlertStatus.choices, default=AlertStatus.OPEN)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acknowledged_alerts",
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["organization", "status", "-created_at"])]

    def __str__(self):
        return self.title
