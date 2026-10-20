"""Notification queue, recording requests, evidence registration, SIEM enqueue."""

from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.events.models import DetectionEvent, Severity

from .models import (
    NotificationChannel,
    NotificationJob,
    NotificationStatus,
    RecordingJob,
    RecordingStatus,
    RecordingVendor,
    SIEMForwardJob,
    SIEMTarget,
    SnapshotObject,
)

logger = logging.getLogger(__name__)

CRITICAL_LIKE = {Severity.CRITICAL, "critical", "emergency"}


def enqueue_event_notifications(event: DetectionEvent) -> dict:
    """Queue notification jobs for critical/safety events and dispatch Celery workers."""
    if event.severity not in CRITICAL_LIKE and event.event_type not in {
        "fire",
        "smoke",
        "weapon",
        "fall",
        "intrusion",
        "emergency_incident",
    }:
        return {"ok": True, "queued": 0}

    org = event.organization
    destinations = (org.settings or {}).get("notification_channels") or [
        {"channel": NotificationChannel.EMAIL, "destination": "ops@example.com"},
        {"channel": NotificationChannel.WEBHOOK, "destination": "/hooks/security"},
    ]
    created = 0
    for item in destinations:
        channel = item.get("channel", NotificationChannel.EMAIL)
        destination = item.get("destination", "")
        rate_key = f"{org.id}:{channel}:{destination}"
        job = NotificationJob.objects.create(
            organization=org,
            event=event,
            channel=channel,
            destination=destination,
            subject=f"[{event.severity.upper()}] {event.event_type} @ {event.camera.name}",
            body=f"Event {event.id} confidence={event.confidence:.2f}",
            status=NotificationStatus.QUEUED,
            payload={
                "event_type": event.event_type,
                "camera_id": str(event.camera_id),
                "severity": event.severity,
                "event_id": str(event.id),
            },
            rate_limit_key=rate_key,
            next_attempt_at=timezone.now(),
        )
        _dispatch_notification(job)
        created += 1
    return {"ok": True, "queued": created}


def _dispatch_notification(job: NotificationJob) -> None:
    try:
        from apps.ops.tasks import send_notification_job

        async_result = send_notification_job.delay(str(job.id))
        job.celery_task_id = getattr(async_result, "id", "") or ""
        if job.celery_task_id:
            job.save(update_fields=["celery_task_id", "updated_at"])
    except Exception as exc:
        logger.warning("Celery dispatch failed for notification %s: %s", job.id, exc)


def request_recording_for_event(event: DetectionEvent) -> dict:
    """Create a recording job and dispatch adapter worker."""
    if event.severity not in CRITICAL_LIKE and event.event_type not in {"fire", "weapon", "smoke"}:
        return {"ok": True, "requested": False}

    existing = RecordingJob.objects.filter(
        event=event,
        status__in=[RecordingStatus.REQUESTED, RecordingStatus.RECORDING, RecordingStatus.READY],
    ).first()
    if existing:
        return {"ok": True, "requested": False, "job_id": str(existing.id)}

    vendor = RecordingVendor.STUB
    if event.camera.rtsp_url:
        vendor = RecordingVendor.RTSP
    org_vendor = (event.organization.settings or {}).get("recording_vendor")
    if org_vendor in {c.value for c in RecordingVendor}:
        vendor = org_vendor

    job = RecordingJob.objects.create(
        organization=event.organization,
        camera=event.camera,
        event=event,
        vendor=vendor,
        status=RecordingStatus.REQUESTED,
        details={"duration_sec": 10, "reason": event.event_type},
    )
    try:
        from apps.ops.tasks import process_recording_job

        process_recording_job.delay(str(job.id))
    except Exception as exc:
        logger.warning("Celery recording dispatch failed for %s: %s", job.id, exc)
    return {"ok": True, "requested": True, "job_id": str(job.id)}


def enqueue_siem_forward(event: DetectionEvent) -> dict:
    """Enqueue SIEM forwards based on organization.settings.siem_targets."""
    targets = (event.organization.settings or {}).get("siem_targets") or []
    if not targets:
        return {"ok": True, "queued": 0}

    from apps.ops.siem import build_siem_payload

    payload = build_siem_payload(event)
    created = 0
    for item in targets:
        target = item.get("target", SIEMTarget.WEBHOOK)
        destination = item.get("destination", "")
        if not destination:
            continue
        job = SIEMForwardJob.objects.create(
            organization=event.organization,
            event=event,
            target=target,
            destination=destination,
            status=NotificationStatus.QUEUED,
            payload=payload,
        )
        try:
            from apps.ops.tasks import forward_siem_event

            forward_siem_event.delay(str(job.id))
        except Exception as exc:
            logger.warning("Celery SIEM dispatch failed for %s: %s", job.id, exc)
        created += 1
    return {"ok": True, "queued": created}


def register_snapshot(
    *,
    organization,
    camera,
    snapshot_key: str,
    snapshot_url: str = "",
    thumbnail_url: str = "",
    event: DetectionEvent | None = None,
    content_type: str = "image/jpeg",
    mime_type: str = "",
    checksum: str = "",
    width: int | None = None,
    height: int | None = None,
    size_bytes: int = 0,
    uploaded_by_edge: bool = True,
    storage_backend: str = "local",
    ttl_hours: int | None = None,
    metadata: dict | None = None,
) -> SnapshotObject:
    ttl = ttl_hours if ttl_hours is not None else settings.EVIDENCE_DEFAULT_TTL_HOURS
    expires_at = timezone.now() + timedelta(hours=ttl)
    mime = mime_type or content_type
    obj = SnapshotObject.objects.create(
        organization=organization,
        camera=camera,
        event=event,
        snapshot_key=snapshot_key,
        snapshot_url=snapshot_url
        or f"{getattr(settings, 'MEDIA_URL', '/media/')}{snapshot_key.lstrip('/')}",
        thumbnail_url=thumbnail_url,
        content_type=content_type,
        mime_type=mime,
        checksum=checksum,
        width=width,
        height=height,
        size_bytes=size_bytes,
        expires_at=expires_at,
        uploaded_by_edge=uploaded_by_edge,
        storage_backend=storage_backend,
        metadata=metadata or {},
    )
    if event is not None:
        event.snapshot_key = obj.snapshot_key
        event.snapshot_url = obj.snapshot_url
        event.save(update_fields=["snapshot_key", "snapshot_url", "updated_at"])
    return obj


def store_and_register_upload(
    *,
    organization,
    camera,
    file_obj,
    event: DetectionEvent | None = None,
    content_type: str = "image/jpeg",
    uploaded_by_edge: bool = True,
) -> SnapshotObject:
    """Upload bytes to evidence backend and register SnapshotObject with signed URL."""
    from apps.ops.storage import put_file_obj

    key = f"snapshots/{camera.id}/{timezone.now().strftime('%Y%m%d%H%M%S')}_{getattr(file_obj, 'name', 'frame.jpg')}"
    stored = put_file_obj(key, file_obj, content_type=content_type)
    return register_snapshot(
        organization=organization,
        camera=camera,
        snapshot_key=stored.key,
        snapshot_url=stored.url,
        event=event,
        content_type=stored.content_type,
        mime_type=stored.content_type,
        checksum=stored.checksum,
        width=stored.width,
        height=stored.height,
        size_bytes=stored.size_bytes,
        uploaded_by_edge=uploaded_by_edge,
        storage_backend=stored.backend,
        metadata={"uploaded_via": "api"},
    )


def refresh_signed_url(snapshot: SnapshotObject) -> str:
    from apps.ops.storage import get_evidence_storage

    storage = get_evidence_storage()
    url = storage.signed_url(snapshot.snapshot_key)
    snapshot.snapshot_url = url
    snapshot.save(update_fields=["snapshot_url", "updated_at"])
    return url
