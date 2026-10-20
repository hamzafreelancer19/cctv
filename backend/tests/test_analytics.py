"""M4 analytics API tests."""

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.alerts.models import AlertRule
from apps.analytics.models import AnalyticsRule, RiskLevel, RuleAction
from apps.analytics.services import process_m4_ingest
from apps.cameras.models import Camera, EdgeDevice
from apps.events.models import DetectionEvent, EventType, Severity
from apps.sites.models import Site, Zone
from apps.tenancy.models import Organization, Role, UserMembership
from django.contrib.auth.models import User


@pytest.fixture
def m4_env(db):
    org = Organization.objects.create(name="M4 Org", slug="m4-org")
    site = Site.objects.create(organization=org, name="HQ", timezone="UTC")
    zone = Zone.objects.create(
        site=site,
        name="Warehouse",
        polygon_json=[[0, 0], [1, 0], [1, 1], [0, 1]],
        is_restricted=True,
        priority="critical",
        loitering_seconds=120,
        max_occupancy=5,
        access_start=timezone.datetime.strptime("09:00", "%H:%M").time(),
        access_end=timezone.datetime.strptime("18:00", "%H:%M").time(),
    )
    cam = Camera.objects.create(site=site, name="Cam1", zone=zone, rtsp_url="rtsp://x", status="online")
    zone.linked_cameras.add(cam)
    user = User.objects.create_user("m4admin", password="pass123")
    UserMembership.objects.create(user=user, organization=org, role=Role.OWNER)
    EdgeDevice.objects.create(
        site=site,
        name="edge",
        api_key_hash=EdgeDevice.hash_api_key("edge-key"),
        api_key_prefix="edge",
        status="online",
    )
    return {"org": org, "site": site, "zone": zone, "cam": cam, "user": user}


@pytest.mark.django_db
def test_loiter_and_crowd_and_rules(m4_env):
    org, cam, zone = m4_env["org"], m4_env["cam"], m4_env["zone"]
    rule = AnalyticsRule.objects.create(
        organization=org,
        name="AfterHoursIntrusion",
        event_types=["intrusion"],
        zone=zone,
        time_start=None,
        time_end=None,
        risk_level=RiskLevel.CRITICAL,
    )
    RuleAction.objects.create(rule=rule, action_type="alert")

    loiter = DetectionEvent.objects.create(
        camera=cam,
        zone=zone,
        event_type=EventType.LOITERING,
        severity=Severity.WARNING,
        confidence=0.9,
        payload={"activity": "loitering", "dwell_seconds": 130, "threshold_seconds": 120, "track_id": 7},
    )
    process_m4_ingest(loiter)
    from apps.analytics.models import LoiterEvent

    assert LoiterEvent.objects.filter(camera=cam).exists()

    crowd = DetectionEvent.objects.create(
        camera=cam,
        zone=zone,
        event_type=EventType.CROWD,
        severity=Severity.CRITICAL,
        confidence=1.0,
        payload={"occupancy": 9, "max_occupancy": 5, "density": 2.1, "over_capacity": True, "heatmap": []},
    )
    process_m4_ingest(crowd)

    intrusion = DetectionEvent.objects.create(
        camera=cam,
        zone=zone,
        event_type=EventType.INTRUSION,
        severity=Severity.CRITICAL,
        confidence=0.95,
        payload={"restricted": True},
    )
    result = process_m4_ingest(intrusion)
    assert result["rules_matched"] >= 1

    client = APIClient()
    client.force_authenticate(user=m4_env["user"])
    r = client.get("/api/v1/loiter-events/")
    assert r.status_code == 200
    assert r.data["count"] >= 1
    r2 = client.get(f"/api/v1/crowd/summary/?organization={org.id}")
    assert r2.status_code == 200
    assert r2.data["current_occupancy"] >= 1
    r3 = client.get("/api/v1/risk-incidents/")
    assert r3.status_code == 200
    r4 = client.post(
        "/api/v1/rules/",
        {
            "organization": str(org.id),
            "name": "WarehouseLoiter",
            "event_types": ["loitering"],
            "zone": str(zone.id),
            "risk_level": "critical",
            "actions": [{"action_type": "alert", "config": {}, "is_active": True}],
        },
        format="json",
    )
    assert r4.status_code == 201


@pytest.mark.django_db
def test_correlation_unknown_loiter_intrusion(m4_env):
    cam, zone = m4_env["cam"], m4_env["zone"]
    DetectionEvent.objects.create(
        camera=cam, zone=zone, event_type=EventType.UNKNOWN_PERSON, severity=Severity.WARNING, confidence=0.8
    )
    DetectionEvent.objects.create(
        camera=cam,
        zone=zone,
        event_type=EventType.LOITERING,
        severity=Severity.WARNING,
        confidence=0.8,
        payload={"activity": "loitering"},
    )
    last = DetectionEvent.objects.create(
        camera=cam, zone=zone, event_type=EventType.INTRUSION, severity=Severity.CRITICAL, confidence=0.9
    )
    result = process_m4_ingest(last)
    assert result["correlated"] is True
    from apps.analytics.models import RiskIncident

    assert RiskIncident.objects.filter(organization=m4_env["org"]).exists()
