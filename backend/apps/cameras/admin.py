from django.contrib import admin

from .models import Camera, EdgeDevice, VisionCapture


@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ("name", "site", "status", "is_active", "auto_record", "last_seen_at")
    list_filter = ("status", "is_active", "auto_record", "site__organization")
    search_fields = ("name",)


@admin.register(EdgeDevice)
class EdgeDeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "site", "status", "last_seen_at", "version")
    list_filter = ("status", "is_active")
    readonly_fields = ("api_key_hash", "api_key_prefix")


@admin.register(VisionCapture)
class VisionCaptureAdmin(admin.ModelAdmin):
    list_display = ("camera", "provider", "model_name", "confidence", "created_at")
    list_filter = ("provider", "organization")
    search_fields = ("summary", "scene", "camera__name")
    readonly_fields = ("raw_response",)
