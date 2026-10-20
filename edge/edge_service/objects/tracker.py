"""M4 Object left / removed detection via stationary object tracking."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from edge_service.types import BoundingBox, Detection


OBJECT_CLASSES = {"bag", "backpack", "handbag", "suitcase", "laptop", "box", "package", "bottle", "chair"}


@dataclass
class ObjectTrack:
    track_id: int
    class_name: str
    bbox: BoundingBox
    confidence: float
    first_seen: float
    last_seen: float
    stationary_since: float | None = None
    left_emitted: bool = False
    removed_emitted: bool = False
    last_center: tuple[float, float] = (0.0, 0.0)


@dataclass
class ObjectAnalyticsEvent:
    event_type: str  # object_left | object_removed
    severity: str
    track_id: int
    object_class: str
    confidence: float
    dwell_seconds: float
    payload: dict[str, Any] = field(default_factory=dict)


def _iou(a: BoundingBox, b: BoundingBox) -> float:
    ax1, ay1, ax2, ay2 = a.as_xyxy()
    bx1, by1, bx2, by2 = b.as_xyxy()
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(1.0, (ax2 - ax1) * (ay2 - ay1))
    area_b = max(1.0, (bx2 - bx1) * (by2 - by1))
    return inter / (area_a + area_b - inter)


class ObjectStateTracker:
    """
    Track non-person objects. Left-behind = stationary beyond threshold.
    Removed = previously stationary object disappears.
    """

    def __init__(self, left_seconds: float = 20.0, max_miss: float = 3.0, iou_thresh: float = 0.3):
        self.left_seconds = left_seconds
        self.max_miss = max_miss
        self.iou_thresh = iou_thresh
        self._tracks: dict[int, ObjectTrack] = {}
        self._next_id = 1
        self._stationary_memory: list[ObjectTrack] = []

    def update(self, detections: list[Detection], now: float | None = None) -> list[ObjectAnalyticsEvent]:
        now = now if now is not None else time.time()
        obj_dets = [d for d in detections if d.class_name.lower() in OBJECT_CLASSES]
        # If detector only emits persons, synthesize demo bags occasionally is NOT done here —
        # pipeline may pass simulated object detections separately.
        matched: set[int] = set()
        used_det: set[int] = set()

        for tid, tr in self._tracks.items():
            best_i, best_iou = -1, 0.0
            for i, det in enumerate(obj_dets):
                if i in used_det:
                    continue
                iou = _iou(tr.bbox, det.bbox)
                if iou > best_iou:
                    best_iou, best_i = iou, i
            if best_i >= 0 and best_iou >= self.iou_thresh:
                det = obj_dets[best_i]
                used_det.add(best_i)
                matched.add(tid)
                cx = (det.bbox.x1 + det.bbox.x2) / 2
                cy = (det.bbox.y1 + det.bbox.y2) / 2
                moved = abs(cx - tr.last_center[0]) + abs(cy - tr.last_center[1])
                tr.bbox = det.bbox
                tr.confidence = det.confidence
                tr.last_seen = now
                tr.class_name = det.class_name
                if moved < 8:
                    if tr.stationary_since is None:
                        tr.stationary_since = now
                else:
                    tr.stationary_since = None
                    tr.left_emitted = False
                tr.last_center = (cx, cy)

        # new tracks
        for i, det in enumerate(obj_dets):
            if i in used_det:
                continue
            if det.class_name.lower() == "person" or det.class_id == 0:
                continue
            tid = self._next_id
            self._next_id += 1
            cx = (det.bbox.x1 + det.bbox.x2) / 2
            cy = (det.bbox.y1 + det.bbox.y2) / 2
            self._tracks[tid] = ObjectTrack(
                track_id=tid,
                class_name=det.class_name,
                bbox=det.bbox,
                confidence=det.confidence,
                first_seen=now,
                last_seen=now,
                stationary_since=now,
                last_center=(cx, cy),
            )
            matched.add(tid)

        events: list[ObjectAnalyticsEvent] = []
        # left behind
        for tid, tr in list(self._tracks.items()):
            if tr.stationary_since and not tr.left_emitted:
                dwell = now - tr.stationary_since
                if dwell >= self.left_seconds:
                    tr.left_emitted = True
                    events.append(
                        ObjectAnalyticsEvent(
                            event_type="object_left",
                            severity="warning",
                            track_id=tr.track_id,
                            object_class=tr.class_name,
                            confidence=tr.confidence,
                            dwell_seconds=round(dwell, 2),
                            payload={"bbox": tr.bbox.as_xywh(), "object_class": tr.class_name},
                        )
                    )
                    self._stationary_memory.append(tr)

        # removed: unmatched tracks past miss window that were left behind
        for tid, tr in list(self._tracks.items()):
            if tid in matched:
                continue
            if now - tr.last_seen < self.max_miss:
                continue
            if tr.left_emitted and not tr.removed_emitted:
                tr.removed_emitted = True
                events.append(
                    ObjectAnalyticsEvent(
                        event_type="object_removed",
                        severity="critical",
                        track_id=tr.track_id,
                        object_class=tr.class_name,
                        confidence=tr.confidence,
                        dwell_seconds=round(now - tr.first_seen, 2),
                        payload={"bbox": tr.bbox.as_xywh(), "object_class": tr.class_name, "was_left_behind": True},
                    )
                )
            del self._tracks[tid]

        return events
