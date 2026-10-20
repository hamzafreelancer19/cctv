from django.urls import path

from .views import (
    EmergencyIncidentActionView,
    EmergencyIncidentListView,
    FallEventListView,
    FireEventListView,
    PPEEventListView,
    SafetyProfileDetailView,
    SafetyProfileListCreateView,
    SafetySummaryView,
    SmokeEventListView,
    WeaponEventListView,
)

urlpatterns = [
    path("fire-events/", FireEventListView.as_view(), name="fire-event-list"),
    path("smoke-events/", SmokeEventListView.as_view(), name="smoke-event-list"),
    path("weapon-events/", WeaponEventListView.as_view(), name="weapon-event-list"),
    path("fall-events/", FallEventListView.as_view(), name="fall-event-list"),
    path("ppe-events/", PPEEventListView.as_view(), name="ppe-event-list"),
    path("safety-profiles/", SafetyProfileListCreateView.as_view(), name="safety-profile-list"),
    path(
        "safety-profiles/<uuid:pk>/",
        SafetyProfileDetailView.as_view(),
        name="safety-profile-detail",
    ),
    path(
        "emergency-incidents/",
        EmergencyIncidentListView.as_view(),
        name="emergency-incident-list",
    ),
    path(
        "emergency-incidents/<uuid:pk>/<str:action>/",
        EmergencyIncidentActionView.as_view(),
        name="emergency-incident-action",
    ),
    path("safety/summary/", SafetySummaryView.as_view(), name="safety-summary"),
]
