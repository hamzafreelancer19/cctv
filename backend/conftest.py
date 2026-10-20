import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.cameras.models import Camera, EdgeDevice
from apps.sites.models import Site
from apps.tenancy.models import Organization, Role, UserMembership


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Test Org", slug="test-org")


@pytest.fixture
def site(org):
    return Site.objects.create(organization=org, name="Test Site", address="123 Test St")


@pytest.fixture
def admin_user(org):
    user = User.objects.create_user(username="testadmin", password="testpass123")
    UserMembership.objects.create(user=user, organization=org, role=Role.ADMIN)
    return user


@pytest.fixture
def camera(site):
    return Camera.objects.create(site=site, name="Cam 1", rtsp_url="rtsp://test", status="online")


@pytest.fixture
def edge_device(site):
    key = "test-edge-key"
    return EdgeDevice.objects.create(
        site=site,
        name="Edge 1",
        api_key_hash=EdgeDevice.hash_api_key(key),
        api_key_prefix=key[:8],
        status="online",
    ), key
