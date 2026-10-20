from django.contrib import admin

from .models import (
    NotificationDeliveryLog,
    NotificationJob,
    PasswordPolicy,
    RecordingJob,
    SessionPolicy,
    SIEMForwardJob,
    SnapshotObject,
    SSOProvider,
)


@admin.register(NotificationJob)
class NotificationJobAdmin(admin.ModelAdmin):
    list_display = ("channel", "destination", "status", "attempts", "created_at")
    list_filter = ("channel", "status")


@admin.register(NotificationDeliveryLog)
class NotificationDeliveryLogAdmin(admin.ModelAdmin):
    list_display = ("job", "attempt", "success", "latency_ms", "created_at")
    list_filter = ("success",)


@admin.register(RecordingJob)
class RecordingJobAdmin(admin.ModelAdmin):
    list_display = ("camera", "vendor", "status", "created_at")
    list_filter = ("vendor", "status")


@admin.register(SnapshotObject)
class SnapshotObjectAdmin(admin.ModelAdmin):
    list_display = ("camera", "snapshot_key", "storage_backend", "expires_at", "created_at")
    list_filter = ("storage_backend",)


@admin.register(SSOProvider)
class SSOProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "protocol", "mfa_required", "is_active")
    list_filter = ("protocol", "is_active")


@admin.register(PasswordPolicy)
class PasswordPolicyAdmin(admin.ModelAdmin):
    list_display = ("organization", "min_length", "max_age_days", "lockout_threshold")


@admin.register(SessionPolicy)
class SessionPolicyAdmin(admin.ModelAdmin):
    list_display = ("organization", "idle_timeout_minutes", "mfa_required", "single_session")


@admin.register(SIEMForwardJob)
class SIEMForwardJobAdmin(admin.ModelAdmin):
    list_display = ("target", "destination", "status", "attempts", "created_at")
    list_filter = ("target", "status")
