from django.contrib import admin

from .models import AnalyticsRule, CrowdStatistic, LoiterEvent, ObjectEvent, RiskIncident, RuleAction


class RuleActionInline(admin.TabularInline):
    model = RuleAction
    extra = 0


@admin.register(AnalyticsRule)
class AnalyticsRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "risk_level", "is_active", "priority")
    list_filter = ("is_active", "risk_level")
    inlines = [RuleActionInline]


@admin.register(LoiterEvent)
class LoiterEventAdmin(admin.ModelAdmin):
    list_display = ("camera", "zone", "dwell_seconds", "escalation_count", "severity", "created_at")
    list_filter = ("severity",)


@admin.register(CrowdStatistic)
class CrowdStatisticAdmin(admin.ModelAdmin):
    list_display = ("camera", "occupancy", "over_capacity", "recorded_at")


@admin.register(ObjectEvent)
class ObjectEventAdmin(admin.ModelAdmin):
    list_display = ("kind", "object_class", "camera", "confidence", "created_at")
    list_filter = ("kind",)


@admin.register(RiskIncident)
class RiskIncidentAdmin(admin.ModelAdmin):
    list_display = ("title", "risk_level", "risk_score", "status", "created_at")
    list_filter = ("risk_level", "status")
