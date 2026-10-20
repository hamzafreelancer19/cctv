from django.contrib import admin

from .models import (
    AttendanceRecord,
    BiometricConsent,
    FaceEmbedding,
    FaceImage,
    Person,
    PersonSighting,
    UnknownSighting,
    VisitorRegistration,
)


class FaceImageInline(admin.TabularInline):
    model = FaceImage
    extra = 0


class FaceEmbeddingInline(admin.TabularInline):
    model = FaceEmbedding
    extra = 0
    readonly_fields = ("vector",)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("full_name", "person_type", "organization", "external_id", "is_active")
    list_filter = ("person_type", "is_active", "organization")
    search_fields = ("full_name", "external_id", "email")
    inlines = [FaceImageInline, FaceEmbeddingInline]


@admin.register(BiometricConsent)
class BiometricConsentAdmin(admin.ModelAdmin):
    list_display = ("person", "consent_type", "granted_at", "revoked_at")


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("person", "direction", "recorded_at", "is_late", "is_overtime", "confidence")
    list_filter = ("direction", "is_late", "organization")


@admin.register(VisitorRegistration)
class VisitorRegistrationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "host_name", "status", "site", "valid_from", "valid_until")
    list_filter = ("status", "organization")


@admin.register(UnknownSighting)
class UnknownSightingAdmin(admin.ModelAdmin):
    list_display = ("organization", "camera", "confidence", "reviewed", "created_at")
    list_filter = ("reviewed", "organization")


@admin.register(PersonSighting)
class PersonSightingAdmin(admin.ModelAdmin):
    list_display = ("person", "camera", "match_score", "confidence", "created_at")
    list_filter = ("organization",)
