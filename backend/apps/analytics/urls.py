from django.urls import path

from .views import (
    AnalyticsRuleDetailView,
    AnalyticsRuleListCreateView,
    CrowdListView,
    CrowdSummaryView,
    IncidentTimelineView,
    LoiterEventListView,
    ObjectEventListView,
    RiskIncidentActionView,
    RiskIncidentListView,
    ZoneAnalyticsDetailView,
    ZoneAnalyticsListCreateView,
)

urlpatterns = [
    # Zones already exist under sites; analytics-enriched endpoints alias for M4 docs
    path("analytics/zones/", ZoneAnalyticsListCreateView.as_view(), name="analytics-zone-list"),
    path("analytics/zones/<uuid:pk>/", ZoneAnalyticsDetailView.as_view(), name="analytics-zone-detail"),
    path("loiter-events/", LoiterEventListView.as_view(), name="loiter-list"),
    path("crowd/", CrowdListView.as_view(), name="crowd-list"),
    path("crowd/summary/", CrowdSummaryView.as_view(), name="crowd-summary"),
    path("object-events/", ObjectEventListView.as_view(), name="object-event-list"),
    path("risk-incidents/", RiskIncidentListView.as_view(), name="risk-incident-list"),
    path("risk-incidents/<uuid:pk>/<str:action>/", RiskIncidentActionView.as_view(), name="risk-incident-action"),
    path("rules/", AnalyticsRuleListCreateView.as_view(), name="analytics-rule-list"),
    path("rules/<uuid:pk>/", AnalyticsRuleDetailView.as_view(), name="analytics-rule-detail"),
    path("incidents/timeline/", IncidentTimelineView.as_view(), name="incident-timeline"),
]
