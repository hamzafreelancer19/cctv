from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "resource_type", "actor", "organization", "created_at")
    list_filter = ("action", "resource_type")
    readonly_fields = ("created_at",)
