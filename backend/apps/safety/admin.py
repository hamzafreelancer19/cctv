from django.contrib import admin

from .models import (
    EmergencyAction,
    EmergencyIncident,
    FallEvent,
    FireEvent,
    PPEEvent,
    SafetyProfile,
    SmokeEvent,
    WeaponEvent,
)


@admin.register(SafetyProfile)
class SafetyProfileAdmin(admin.ModelAdmin):
    list_display = ("camera", "environment", "fire_threshold", "smoke_threshold", "is_active")


for model in (FireEvent, SmokeEvent, WeaponEvent, FallEvent, PPEEvent):
    admin.site.register(model)


class EmergencyActionInline(admin.TabularInline):
    model = EmergencyAction
    extra = 0


@admin.register(EmergencyIncident)
class EmergencyIncidentAdmin(admin.ModelAdmin):
    list_display = ("title", "severity", "status", "site", "created_at")
    list_filter = ("severity", "status")
    inlines = [EmergencyActionInline]
