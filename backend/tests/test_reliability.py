"""Priority-1 reliability: dedupe, zone validation, unified ingest."""

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.cameras.models import Camera, EdgeDevice
from apps.events.models import DetectionEvent, EventType, Severity
from apps.events.pipeline import IngestValidationError, create_detection_event, validate_zone_for_camera
from apps.ops.models import NotificationJob, RecordingJob
from apps.sites.models import Site, Zone
from apps.tenancy.models import Organization, Role, UserMembership


@pytest.fixture
def reliability_env(db):
    org = Organization.objects.create(name="Rel Org", slug="rel-org", settings={})
    site = Site.objects.create(organization=org, name="HQ")
    zone = Zone.objects.create(
        site=site,
        name="Restricted",
        polygon_json=[[0, 0], [1, 0], [1, 1], [0, 1]],
        is_restricted=True,
        config_version=3,
    )
    other_site = Site.objects.create(organization=org, name="Other")
    other_zone = Zone.objects.create(
        site=other_site,
        name="Wrong Site Zone",
        polygon_json=[[0, 0], [1, 0], [1, 1], [0, 1]],
        is_restricted=True,
    )
    camera = Camera.objects.create(site=site, zone=zone, name="Cam", rtsp_url="rtsp://x", status="online")
    key = "rel-edge-key"
    device = EdgeDevice.objects.create(
        site=site,
        name="Edge",
        api_key_hash=EdgeDevice.hash_api_key(key),
        api_key_prefix="rel",
        status="online",
    )
    user = User.objects.create_user("reladmin", password="pass")
    UserMembership.objects.create(user=user, organization=org, role=Role.OWNER)
    return {
        "org": org,
        "site": site,
        "zone": zone,
        "other_zone": other_zone,
        "camera": camera,
        "device": device,
        "key": key,
        "user": user,
    }


@pytest.mark.django_db
def test_composite_dedupe_returns_200(reliability_env):
    client = APIClient()
    payload = {
        "camera_id": str(reliability_env["camera"].id),
        "event_type": "person_detected",
        "severity": "info",
        "confidence": 0.9,
        "edge_event_id": "edge-unique-1",
        "payload": {},
    }
    r1 = client.post("/api/v1/events/ingest/", payload, format="json", HTTP_X_EDGE_API_KEY=reliability_env["key"])
    r2 = client.post("/api/v1/events/ingest/", payload, format="json", HTTP_X_EDGE_API_KEY=reliability_env["key"])
    assert r1.status_code == 201
    assert r2.status_code == 200
    assert r1.data["id"] == r2.data["id"]
    assert DetectionEvent.objects.filter(edge_event_id="edge-unique-1").count() == 1
    event = DetectionEvent.objects.get(edge_event_id="edge-unique-1")
    assert event.edge_device_id == reliability_env["device"].id


@pytest.mark.django_db
def test_zone_must_belong_to_camera_site(reliability_env):
    camera = reliability_env["camera"]
    with pytest.raises(IngestValidationError) as exc:
        validate_zone_for_camera(camera, reliability_env["other_zone"].id, event_type=EventType.INTRUSION)
    assert exc.value.code == "ZONE_SITE_MISMATCH"


@pytest.mark.django_db
def test_zone_version_and_restricted_type(reliability_env):
    camera = reliability_env["camera"]
    zone = reliability_env["zone"]
    with pytest.raises(IngestValidationError) as exc:
        validate_zone_for_camera(camera, zone.id, event_type=EventType.INTRUSION, zone_version=1)
    assert exc.value.code == "ZONE_VERSION_MISMATCH"

    lobby = Zone.objects.create(
        site=reliability_env["site"],
        name="Lobby",
        polygon_json=[[0, 0], [1, 0], [1, 1], [0, 1]],
        is_restricted=False,
    )
    with pytest.raises(IngestValidationError) as exc2:
        validate_zone_for_camera(camera, lobby.id, event_type=EventType.INTRUSION)
    assert exc2.value.code == "ZONE_TYPE_MISMATCH"


@pytest.mark.django_db
def test_unified_pipeline_queues_ops_jobs(reliability_env):
    result = create_detection_event(
        camera=reliability_env["camera"],
        event_type=EventType.FIRE,
        severity=Severity.CRITICAL,
        confidence=0.95,
        edge_event_id="fire-1",
        edge_device=reliability_env["device"],
        zone_id=reliability_env["zone"].id,
        zone_version=3,
        payload={"verified": True},
    )
    assert result.created is True
    assert NotificationJob.objects.filter(event=result.event).exists()
    assert RecordingJob.objects.filter(event=result.event).exists()
