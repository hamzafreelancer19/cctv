"""Identity / face recognition API tests."""

import pytest
from django.utils import timezone
from rest_framework import status

from apps.identity.embeddings import simulate_embedding_from_bytes, best_match
from apps.identity.models import BiometricConsent, FaceEmbedding, Person, PersonType, UnknownSighting


@pytest.mark.django_db
def test_person_enroll_and_match(api_client, admin_user, org, camera, edge_device):
    api_client.force_authenticate(user=admin_user)
    person = Person.objects.create(
        organization=org,
        full_name="Test User",
        person_type=PersonType.EMPLOYEE,
        external_id="EMP-T1",
    )
    BiometricConsent.objects.create(organization=org, person=person, granted_at=timezone.now())
    emb = simulate_embedding_from_bytes(b"test-user-face")

    enroll = api_client.post(
        "/api/v1/persons/enroll/",
        {"person_id": str(person.id), "embedding": emb, "quality_score": 0.9, "blur_score": 150},
        format="json",
    )
    assert enroll.status_code == status.HTTP_201_CREATED

    device, key = edge_device
    match = api_client.post(
        "/api/v1/face/match/",
        {
            "camera_id": str(camera.id),
            "embedding": emb,
            "threshold": 0.4,
            "create_attendance": True,
            "create_unknown_if_miss": True,
        },
        format="json",
        HTTP_X_EDGE_API_KEY=key,
    )
    assert match.status_code == status.HTTP_200_OK
    assert match.data["match"] is True
    assert match.data["full_name"] == "Test User"
    assert match.data["attendance_id"] is not None


@pytest.mark.django_db
def test_unknown_face_creates_sighting(api_client, camera, edge_device, org, admin_user):
    device, key = edge_device
    # Ensure org has no matching embedding
    emb = simulate_embedding_from_bytes(b"completely-unknown-face-xyz")
    resp = api_client.post(
        "/api/v1/face/match/",
        {
            "camera_id": str(camera.id),
            "embedding": emb,
            "threshold": 0.99,
            "create_unknown_if_miss": True,
            "track_id": 42,
        },
        format="json",
        HTTP_X_EDGE_API_KEY=key,
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["match"] is False
    assert resp.data["unknown_sighting_id"] is not None
    sighting = UnknownSighting.objects.get(id=resp.data["unknown_sighting_id"])
    assert sighting.gallery_person is None
    assert not Person.objects.filter(organization=org, person_type=PersonType.UNKNOWN).exists()


def test_best_match_threshold():
    a = simulate_embedding_from_bytes(b"same")
    b = simulate_embedding_from_bytes(b"same")
    pid, score = best_match(a, [("p1", b)], threshold=0.9)
    assert pid == "p1"
    assert score > 0.99
