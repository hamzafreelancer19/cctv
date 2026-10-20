from django.contrib import admin

from .models import DetectionEvent


@admin.register(DetectionEvent)
class DetectionEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "camera", "severity", "confidence", "review_status", "created_at")
    list_filter = ("event_type", "severity", "review_status")
    search_fields = ("camera__name", "edge_event_id")
    readonly_fields = ("created_at", "updated_at")
