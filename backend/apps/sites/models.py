from django.db import models

from apps.common.models import TimestampedModel, UUIDModel
from apps.tenancy.models import Organization


class Site(UUIDModel, TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="sites")
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("organization", "name")

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class ZonePriority(models.TextChoices):
    CRITICAL = "critical", "Critical"
    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"


class Zone(UUIDModel, TimestampedModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="zones")
    name = models.CharField(max_length=255)
    polygon_json = models.JSONField(default=list, help_text="List of [x,y] normalized coordinates")
    is_restricted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    # M4 hardening
    priority = models.CharField(max_length=16, choices=ZonePriority.choices, default=ZonePriority.MEDIUM)
    loitering_seconds = models.FloatField(default=120.0)
    visitor_loitering_seconds = models.FloatField(default=60.0)
    ignore_employees = models.BooleanField(default=False)
    max_occupancy = models.PositiveIntegerField(null=True, blank=True)
    # Working hours (site local). Outside window = after-hours.
    access_start = models.TimeField(null=True, blank=True, help_text="Working hours start")
    access_end = models.TimeField(null=True, blank=True, help_text="Working hours end")
    after_hours_restricted = models.BooleanField(default=True)
    # Optional tripwire for entry/exit direction: [[x1,y1],[x2,y2]] normalized
    entry_line_json = models.JSONField(default=list, blank=True)
    linked_cameras = models.ManyToManyField("cameras.Camera", blank=True, related_name="analytics_zones")
    # Bumped when polygon/rules change so edge can detect config drift.
    config_version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["name"]
        unique_together = ("site", "name")

    def __str__(self):
        return f"{self.name} @ {self.site.name}"

    @property
    def organization(self):
        return self.site.organization

    def bump_config_version(self):
        self.config_version = (self.config_version or 0) + 1
        self.save(update_fields=["config_version", "updated_at"])
