"""Sprint 5 — Event builder, cooldown, optional snapshots, control-plane ingest helpers."""

from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path
from typing import Any

from edge_service.types import Detection, FramePacket, Track
from edge_service.zones.engine import ZoneEvent

logger = logging.getLogger(__name__)


def build_person_event(
    camera_id: str,
    track: Track,
    model_name: str,
    model_version: str,
    zone_id: str | None = None,
) -> dict[str, Any]:
    return {
        "camera_id": camera_id,
        "event_type": "person_detected",
        "severity": "info" if track.confidence >= 0.8 else "warning",
        "confidence": float(track.confidence),
        "model_name": model_name,
        "model_version": model_version,
        "zone_id": zone_id,
        "payload": {
            "track_id": track.track_id,
            "bbox": track.bbox.as_xywh(),
            "class_name": track.class_name,
            "m2": True,
        },
        "edge_event_id": str(uuid.uuid4()),
    }


def build_zone_event(
    camera_id: str,
    zone_event: ZoneEvent,
    model_name: str,
    model_version: str,
) -> dict[str, Any]:
    return {
        "camera_id": camera_id,
        "event_type": zone_event.event_type,
        "severity": zone_event.severity,
        "confidence": float(zone_event.confidence),
        "model_name": model_name,
        "model_version": model_version,
        "zone_id": zone_event.zone_id,
        "payload": {
            "track_id": zone_event.track_id,
            "zone_name": zone_event.zone_name,
            **zone_event.payload,
            "m2": True,
        },
        "edge_event_id": str(uuid.uuid4()),
    }


class EventCooldown:
    """Suppress duplicate events for same camera/track/type within cooldown window."""

    def __init__(self, cooldown_sec: float = 15.0):
        self.cooldown_sec = cooldown_sec
        self._last: dict[str, float] = {}

    def allow(self, camera_id: str, event_type: str, track_id: int | None = None, zone_id: str | None = None) -> bool:
        key = f"{camera_id}:{event_type}:{track_id or '-'}:{zone_id or '-'}"
        now = time.time()
        last = self._last.get(key, 0.0)
        if now - last < self.cooldown_sec:
            return False
        self._last[key] = now
        return True


def save_snapshot(frame_packet: FramePacket, track: Track | None, directory: str) -> str | None:
    try:
        import cv2

        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        filename = f"{frame_packet.camera_id}_{int(frame_packet.timestamp)}_{uuid.uuid4().hex[:8]}.jpg"
        out = path / filename
        frame = frame_packet.frame.copy()
        if track is not None:
            x1, y1, x2, y2 = map(int, track.bbox.as_xyxy())
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 255), 2)
            cv2.putText(
                frame,
                f"ID {track.track_id}",
                (x1, max(0, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 200, 255),
                2,
            )
        cv2.imwrite(str(out), frame)
        return str(out)
    except Exception as exc:
        logger.warning("Snapshot failed: %s", exc)
        return None
