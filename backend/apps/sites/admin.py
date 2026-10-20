from django.contrib import admin

from .models import Site, Zone


class ZoneInline(admin.TabularInline):
    model = Zone
    extra = 0


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "timezone", "is_active")
    list_filter = ("organization", "is_active")
    search_fields = ("name", "address")
    inlines = [ZoneInline]


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "site", "is_restricted", "is_active")
    list_filter = ("is_restricted", "is_active")
