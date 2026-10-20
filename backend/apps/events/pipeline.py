"""Unified detection-event ingest, validation, and post-processing."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.cameras.models import Camera, EdgeDevice
from apps.sites.models import Zone

from .models import DetectionEvent, EventType, Severity

logger = logging.getLogger(__name__)


class IngestValidationError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# Event types that require a restricted zone (when a zone is supplied).
RESTRICTED_ZONE_EVENTS = {
    EventType.INTRUSION,
}

# Event types that should not be attached to inactive/mismatched zones.
ZONE_AWARE_EVENTS = {
    EventType.INTRUSION,
    EventType.ZONE_ENTER,
    EventType.ZONE_EXIT,
    EventType.LOITERING,
    EventType.CROWD,
    EventType.ACTIVITY,
    EventType.FIRE,
    EventType.SMOKE,
    EventType.WEAPON,
    EventType.FALL,
    EventType.PPE_VIOLATION,
}


@dataclass
class IngestResult:
    event: DetectionEvent
    created: bool


def validate_zone_for_camera(
    camera: Camera,
    zone_id,
    event_type: str | None = None,
    zone_version: int | None = None,
) -> Zone | None:
    """
    Camera → Camera.Site → Zone.Site validation.

    Rules:
    - Zone belongs to camera's site
    - Zone is active
    - Optional config version matches
    - Restricted events require restricted zones when zone is present
    """
    if not zone_id:
        return None

    zone = Zone.objects.filter(id=zone_id).select_related("site").first()
    if zone is None:
        raise IngestValidationError("ZONE_NOT_FOUND", "Zone not found.", status_code=404)
    if zone.site_id != camera.site_id:
        raise IngestValidationError(
            "ZONE_SITE_MISMATCH",
            "Zone does not belong to the camera's site.",
            status_code=400,
        )
    if not zone.is_active:
        raise IngestValidationError("ZONE_INACTIVE", "Zone is inactive.", status_code=400)

    if zone_version is not None and zone.config_version != int(zone_version):
        raise IngestValidationError(
            "ZONE_VERSION_MISMATCH",
            f"Zone config version {zone.config_version} does not match payload version {zone_version}.",
            status_code=409,
        )

    if event_type in RESTRICTED_ZONE_EVENTS and not zone.is_restricted:
        raise IngestValidationError(
            "ZONE_TYPE_MISMATCH",
            f"Event type '{event_type}' requires a restricted zone.",
            status_code=400,
        )

    return zone


def find_existing_event(
    *,
    camera: Camera,
    edge_event_id: str,
    edge_device: EdgeDevice | None,
) -> DetectionEvent | None:
    if not edge_event_id:
        return None
    qs = DetectionEvent.objects.filter(edge_event_id=edge_event_id)
    if edge_device is not None:
        return qs.filter(edge_device=edge_device).first()
    # Unbound API-key mode: scope by camera to avoid global collisions.
    return qs.filter(camera=camera, edge_device__isnull=True).first()


def run_post_ingest_hooks(event: DetectionEvent) -> dict[str, Any]:
    """
    Single post-ingest pipeline used by edge ingest and internal producers.

    Edge → DetectionEvent → hooks → M3/M4/M5/notifications/reports/audit
    """
    results: dict[str, Any] = {}

    hooks = [
        ("alerts", _hook_alerts),
        ("m4", _hook_m4),
        ("m5", _hook_m5),
        ("notifications", _hook_notifications),
        ("reports", _hook_reports),
        ("audit", _hook_audit),
        ("recording", _hook_recording),
        ("siem", _hook_siem),
        ("metrics", _hook_metrics),
    ]
    for name, hook in hooks:
        try:
            results[name] = hook(event) or {"ok": True}
        except Exception as exc:
            logger.exception("Post-ingest hook %s failed for event %s", name, event.id)
            results[name] = {"ok": False, "error": str(exc)}
    return results


def _hook_alerts(event: DetectionEvent):
    from apps.alerts.services import evaluate_alert_rules

    evaluate_alert_rules(event)
    return {"ok": True}


def _hook_m4(event: DetectionEvent):
    from apps.analytics.services import process_m4_ingest

    return process_m4_ingest(event)


def _hook_m5(event: DetectionEvent):
    from apps.safety.services import process_m5_ingest

    return process_m5_ingest(event)


def _hook_notifications(event: DetectionEvent):
    try:
        from apps.ops.services import enqueue_event_notifications

        return enqueue_event_notifications(event)
    except Exception:
        return {"ok": True, "skipped": True}


def _hook_reports(event: DetectionEvent):
    # Reporting aggregates are query-time for now; hook reserved for M6 workers.
    return {"ok": True, "deferred": True}


def _hook_audit(event: DetectionEvent):
    from apps.audit.models import log_audit

    log_audit(
        action="event.ingested",
        resource_type="detection_event",
        resource_id=str(event.id),
        organization=event.organization,
        details={
            "event_type": event.event_type,
            "camera_id": str(event.camera_id),
            "severity": event.severity,
            "edge_event_id": event.edge_event_id,
        },
    )
    return {"ok": True}


def _hook_recording(event: DetectionEvent):
    try:
        from apps.ops.services import request_recording_for_event

        return request_recording_for_event(event)
    except Exception:
        return {"ok": True, "skipped": True}


def _hook_siem(event: DetectionEvent):
    try:
        from apps.ops.services import enqueue_siem_forward

        return enqueue_siem_forward(event)
    except Exception:
        return {"ok": True, "skipped": True}


def _hook_metrics(event: DetectionEvent):
    try:
        from apps.ops.observability import observe_ingest

        observe_ingest(event.event_type, event.severity)
        return {"ok": True}
    except Exception:
        return {"ok": True, "skipped": True}


def create_detection_event(
    *,
    camera: Camera,
    event_type: str,
    severity: str = Severity.INFO,
    confidence: float = 0.0,
    model_name: str = "",
    model_version: str = "",
    payload: dict | None = None,
    zone_id=None,
    zone_version: int | None = None,
    edge_event_id: str = "",
    edge_device: EdgeDevice | None = None,
    run_hooks: bool = True,
    touch_camera: bool = True,
) -> IngestResult:
    """
    Idempotent create used by edge ingest and internal producers.

    Returns existing event with created=False when (edge_device, edge_event_id) already exists.
    """
    payload = payload or {}
    edge_event_id = (edge_event_id or "").strip()

    existing = find_existing_event(camera=camera, edge_event_id=edge_event_id, edge_device=edge_device)
    if existing:
        return IngestResult(event=existing, created=False)

    zone = None
    if zone_id:
        zone = validate_zone_for_camera(
            camera,
            zone_id,
            event_type=event_type,
            zone_version=zone_version if zone_version is not None else payload.get("zone_version"),
        )
    elif event_type in ZONE_AWARE_EVENTS and camera.zone_id and camera.zone and camera.zone.is_active:
        # Optional default attachment when producer omits zone_id.
        zone = camera.zone

    try:
        with transaction.atomic():
            event = DetectionEvent.objects.create(
                camera=camera,
                zone=zone,
                edge_device=edge_device,
                event_type=event_type,
                severity=severity or Severity.INFO,
                confidence=confidence or 0.0,
                model_name=model_name or "",
                model_version=model_version or "",
                payload=payload,
                edge_event_id=edge_event_id,
            )
    except IntegrityError:
        existing = find_existing_event(camera=camera, edge_event_id=edge_event_id, edge_device=edge_device)
        if existing:
            return IngestResult(event=existing, created=False)
        raise

    if touch_camera:
        camera.last_seen_at = timezone.now()
        camera.status = "online"
        camera.save(update_fields=["last_seen_at", "status", "updated_at"])

    if run_hooks:
        run_post_ingest_hooks(event)

    return IngestResult(event=event, created=True)


def ingest_from_edge_payload(data: dict, edge_device: EdgeDevice | None = None) -> IngestResult:
    camera = (
        Camera.objects.select_related("site__organization", "zone")
        .filter(id=data["camera_id"], is_active=True)
        .first()
    )
    if camera is None:
        raise IngestValidationError("NOT_FOUND", "Camera not found.", status_code=404)

    if edge_device is not None and camera.site_id != edge_device.site_id:
        raise IngestValidationError("FORBIDDEN", "Camera not on edge site.", status_code=403)

    return create_detection_event(
        camera=camera,
        event_type=data["event_type"],
        severity=data.get("severity", Severity.INFO),
        confidence=data.get("confidence", 0.0),
        model_name=data.get("model_name", ""),
        model_version=data.get("model_version", ""),
        payload=data.get("payload") or {},
        zone_id=data.get("zone_id"),
        zone_version=data.get("zone_version"),
        edge_event_id=data.get("edge_event_id", ""),
        edge_device=edge_device,
        run_hooks=True,
        touch_camera=True,
    )
