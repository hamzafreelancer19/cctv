"""Prometheus metrics helpers."""

from __future__ import annotations

from django.db.models import Count

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
except Exception:  # pragma: no cover
    CONTENT_TYPE_LATEST = "text/plain"
    Counter = Gauge = Histogram = None
    generate_latest = None


EVENT_INGEST_TOTAL = (
    Counter("sentinel_event_ingest_total", "Events ingested", ["event_type", "severity"]) if Counter else None
)
NOTIFICATION_FAILURES = (
    Counter("sentinel_notification_failures_total", "Notification delivery failures", ["channel"]) if Counter else None
)
NOTIFICATION_SENT = (
    Counter("sentinel_notification_sent_total", "Notifications sent", ["channel"]) if Counter else None
)
API_LATENCY = (
    Histogram("sentinel_api_latency_seconds", "API latency", ["endpoint"]) if Histogram else None
)
CAMERA_ONLINE = Gauge("sentinel_camera_online", "Online cameras") if Gauge else None
QUEUE_DEPTH = Gauge("sentinel_notification_queue_depth", "Queued notification jobs") if Gauge else None
EVENT_RATE = Gauge("sentinel_event_rate_today", "Events created today") if Gauge else None


def observe_ingest(event_type: str, severity: str):
    if EVENT_INGEST_TOTAL:
        EVENT_INGEST_TOTAL.labels(event_type=event_type, severity=severity).inc()


def observe_notification(success: bool, channel: str):
    if success and NOTIFICATION_SENT:
        NOTIFICATION_SENT.labels(channel=channel).inc()
    elif not success and NOTIFICATION_FAILURES:
        NOTIFICATION_FAILURES.labels(channel=channel).inc()


def refresh_gauges():
    if not Gauge:
        return
    from apps.cameras.models import Camera
    from apps.events.models import DetectionEvent
    from apps.ops.models import NotificationJob, NotificationStatus
    from django.utils import timezone

    CAMERA_ONLINE.set(Camera.objects.filter(status="online", is_active=True).count())
    QUEUE_DEPTH.set(NotificationJob.objects.filter(status=NotificationStatus.QUEUED).count())
    EVENT_RATE.set(DetectionEvent.objects.filter(created_at__date=timezone.now().date()).count())


def render_metrics() -> tuple[bytes, str]:
    refresh_gauges()
    if generate_latest is None:
        return b"# prometheus_client not installed\n", "text/plain; charset=utf-8"
    return generate_latest(), CONTENT_TYPE_LATEST
