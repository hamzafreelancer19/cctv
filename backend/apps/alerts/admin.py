from django.contrib import admin

from .models import Alert, AlertRule


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "event_type", "min_severity", "is_active")
    list_filter = ("event_type", "is_active", "organization")


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("title", "organization", "severity", "status", "created_at")
    list_filter = ("severity", "status", "organization")
