import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.cameras.models import Camera
from apps.events.models import DetectionEvent, EventType, Severity
from apps.safety.models import EmergencyIncident, FallEvent, FireEvent, SmokeEvent
from apps.safety.services import process_m5_ingest
from apps.sites.models import Site, Zone
from apps.tenancy.models import Organization, Role, UserMembership


@pytest.fixture
def safety_env(db):
    organization = Organization.objects.create(name="Safety Org", slug="safety-org")
    site = Site.objects.create(organization=organization, name="Plant", timezone="UTC")
    zone = Zone.objects.create(
        site=site,
        name="Production",
        polygon_json=[[0, 0], [1, 0], [1, 1], [0, 1]],
    )
    camera = Camera.objects.create(
        site=site,
        zone=zone,
        name="Plant Cam",
        rtsp_url="rtsp://example",
        status="online",
    )
    user = User.objects.create_user("safety-admin", password="pass123")
    UserMembership.objects.create(
        user=user,
        organization=organization,
        role=Role.OWNER,
    )
    return {
        "organization": organization,
        "site": site,
        "zone": zone,
        "camera": camera,
        "user": user,
    }


@pytest.mark.django_db
def test_fire_and_smoke_form_one_emergency_incident(safety_env):
    camera = safety_env["camera"]
    zone = safety_env["zone"]
    fire = DetectionEvent.objects.create(
        camera=camera,
        zone=zone,
        event_type=EventType.FIRE,
        severity=Severity.CRITICAL,
        confidence=0.94,
        payload={
            "verified": True,
            "confirmation_frames": 3,
            "environment": "indoor",
            "area_ratio": 0.2,
        },
    )
    process_m5_ingest(fire)
    assert FireEvent.objects.filter(detection_event=fire, verified=True).exists()

    smoke = DetectionEvent.objects.create(
        camera=camera,
        zone=zone,
        event_type=EventType.SMOKE,
        severity=Severity.CRITICAL,
        confidence=0.85,
        payload={
            "density": 0.35,
            "density_level": "high",
            "persistent": True,
            "duration_seconds": 12,
            "trend": "rising",
        },
    )
    process_m5_ingest(smoke)
    assert SmokeEvent.objects.filter(detection_event=smoke, persistent=True).exists()
    incident = EmergencyIncident.objects.get(organization=safety_env["organization"])
    assert incident.severity == "emergency"
    assert incident.title == "Fire / Smoke"
    assert incident.score == 9.0
    assert incident.event_links.count() == 2
    assert incident.continuous_recording_requested is True


@pytest.mark.django_db
def test_fall_recovery_updates_open_fall(safety_env):
    camera = safety_env["camera"]
    fallen = DetectionEvent.objects.create(
        camera=camera,
        event_type=EventType.FALL,
        severity=Severity.CRITICAL,
        confidence=0.9,
        payload={"track_id": 8, "status": "fallen", "duration_seconds": 3},
    )
    process_m5_ingest(fallen)
    recovery = DetectionEvent.objects.create(
        camera=camera,
        event_type=EventType.FALL_RECOVERY,
        severity=Severity.INFO,
        confidence=0.9,
        payload={"track_id": 8, "status": "recovered"},
    )
    process_m5_ingest(recovery)
    fall = FallEvent.objects.get(detection_event=fallen)
    assert fall.status == "recovered"
    assert fall.recovered_at is not None


@pytest.mark.django_db
def test_safety_apis_and_acknowledge(safety_env):
    event = DetectionEvent.objects.create(
        camera=safety_env["camera"],
        event_type=EventType.WEAPON,
        severity=Severity.CRITICAL,
        confidence=0.92,
        payload={"weapon_type": "handgun", "track_id": 3, "associated": True},
    )
    process_m5_ingest(event)
    client = APIClient()
    client.force_authenticate(user=safety_env["user"])
    assert client.get("/api/v1/weapon-events/").status_code == 200
    response = client.get("/api/v1/emergency-incidents/")
    assert response.status_code == 200
    incident_id = response.data["results"][0]["id"]
    acknowledged = client.post(
        f"/api/v1/emergency-incidents/{incident_id}/acknowledge/",
        {},
        format="json",
    )
    assert acknowledged.status_code == 200
    assert acknowledged.data["status"] == "acknowledged"
    assert client.get("/api/v1/safety/summary/").status_code == 200
