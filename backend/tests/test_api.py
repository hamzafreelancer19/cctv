import pytest
from rest_framework import status


@pytest.mark.django_db
def test_health_endpoint(api_client):
    response = api_client.get("/api/v1/health/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "healthy"


@pytest.mark.django_db
def test_jwt_login(api_client, admin_user):
    response = api_client.post("/api/v1/auth/token/", {"username": "testadmin", "password": "testpass123"})
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_tenant_isolation(api_client, org, admin_user, site, camera):
    from apps.cameras.models import Camera
    from apps.sites.models import Site
    from apps.tenancy.models import Organization

    other_org = Organization.objects.create(name="Other Org", slug="other-org")
    other_site = Site.objects.create(organization=other_org, name="Other Site")
    Camera.objects.create(site=other_site, name="Secret Cam")

    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/cameras/")
    assert response.status_code == status.HTTP_200_OK
    names = [c["name"] for c in response.data["results"]]
    assert "Cam 1" in names
    assert "Secret Cam" not in names


@pytest.mark.django_db
def test_event_ingest(api_client, camera, edge_device):
    device, key = edge_device
    payload = {
        "camera_id": str(camera.id),
        "event_type": "person_detected",
        "severity": "warning",
        "confidence": 0.87,
        "model_name": "yolo-sim",
        "model_version": "0.1.0",
        "payload": {"track_id": 1, "bbox": [100, 100, 200, 300]},
        "edge_event_id": "evt-001",
    }
    response = api_client.post(
        "/api/v1/events/ingest/",
        payload,
        format="json",
        HTTP_X_EDGE_API_KEY=key,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["event_type"] == "person_detected"

    # Idempotent ingest
    response2 = api_client.post(
        "/api/v1/events/ingest/",
        payload,
        format="json",
        HTTP_X_EDGE_API_KEY=key,
    )
    assert response2.status_code == status.HTTP_200_OK
    assert response2.data["id"] == response.data["id"]


@pytest.mark.django_db
def test_dashboard_summary(api_client, admin_user, camera):
    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/dashboard/summary/")
    assert response.status_code == status.HTTP_200_OK
    assert "cameras_total" in response.data
    assert response.data["cameras_total"] >= 1


@pytest.mark.django_db
def test_camera_management_and_rtsp_validation(api_client, admin_user, site):
    api_client.force_authenticate(user=admin_user)
    created = api_client.post(
        "/api/v1/cameras/",
        {
            "site": str(site.id),
            "name": "Entrance Camera",
            "rtsp_url": "rtsp://user:pass@192.168.1.10:554/stream1",
            "enabled_modules": ["multi_person_tracking", "intrusion_detection"],
            "is_active": True,
        },
        format="json",
    )
    assert created.status_code == status.HTTP_201_CREATED
    camera_id = created.data["id"]

    updated = api_client.patch(
        f"/api/v1/cameras/{camera_id}/",
        {"name": "Main Entrance"},
        format="json",
    )
    assert updated.status_code == status.HTTP_200_OK
    assert updated.data["name"] == "Main Entrance"

    invalid = api_client.post(
        "/api/v1/cameras/",
        {
            "site": str(site.id),
            "name": "Invalid Stream",
            "rtsp_url": "ftp://example.com/video",
        },
        format="json",
    )
    assert invalid.status_code == status.HTTP_400_BAD_REQUEST

    http_cam = api_client.post(
        "/api/v1/cameras/",
        {
            "site": str(site.id),
            "name": "Phone IP Webcam",
            "rtsp_url": "http://192.168.100.53:8080",
            "enabled_modules": ["multi_person_tracking"],
            "is_active": True,
        },
        format="json",
    )
    assert http_cam.status_code == status.HTTP_201_CREATED
    assert http_cam.data["rtsp_url"].startswith("http://")


@pytest.mark.django_db
def test_camera_connection_test_requires_rtsp(api_client, admin_user, site):
    from apps.cameras.models import Camera

    camera = Camera.objects.create(site=site, name="No Stream", rtsp_url="")
    api_client.force_authenticate(user=admin_user)
    response = api_client.post(f"/api/v1/cameras/{camera.id}/test/", {}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["ok"] is False
