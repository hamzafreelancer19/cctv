"""Sprint 3 — Multi-person IoU tracker (ByteTrack-style lightweight)."""

from __future__ import annotations

import time

from edge_service.types import BoundingBox, Detection, Track


class IOUTracker:
    """Simple multi-object tracker using IoU matching.

    Good enough for M2 without requiring ByteTrack/GMC dependencies.
    Can be replaced with ByteTrack later behind the same interface.
    """

    def __init__(self, iou_threshold: float = 0.3, max_age: int = 30, min_hits: int = 1):
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self.min_hits = min_hits
        self._next_id = 1
        self._tracks: dict[int, Track] = {}

    def update(self, detections: list[Detection], now: float | None = None) -> list[Track]:
        now = now if now is not None else time.time()
        track_ids = list(self._tracks.keys())
        det_used = set()
        track_used = set()

        # Greedy IoU matching
        pairs: list[tuple[float, int, int]] = []
        for tid in track_ids:
            for di, det in enumerate(detections):
                pairs.append((self._tracks[tid].bbox.iou(det.bbox), tid, di))
        pairs.sort(reverse=True, key=lambda x: x[0])

        for iou, tid, di in pairs:
            if iou < self.iou_threshold:
                break
            if tid in track_used or di in det_used:
                continue
            det = detections[di]
            tr = self._tracks[tid]
            tr.bbox = det.bbox
            tr.confidence = det.confidence
            tr.class_name = det.class_name
            tr.hits += 1
            tr.age += 1
            tr.time_since_update = 0
            tr.last_seen_ts = now
            det.track_id = tid
            track_used.add(tid)
            det_used.add(di)

        # New tracks
        for di, det in enumerate(detections):
            if di in det_used:
                continue
            tid = self._next_id
            self._next_id += 1
            self._tracks[tid] = Track(
                track_id=tid,
                bbox=det.bbox,
                confidence=det.confidence,
                class_name=det.class_name,
                age=1,
                hits=1,
                time_since_update=0,
                first_seen_ts=now,
                last_seen_ts=now,
            )
            det.track_id = tid

        # Age unmatched
        for tid in track_ids:
            if tid in track_used:
                continue
            tr = self._tracks[tid]
            tr.time_since_update += 1
            tr.age += 1

        # Remove stale
        stale = [tid for tid, tr in self._tracks.items() if tr.time_since_update > self.max_age]
        for tid in stale:
            del self._tracks[tid]

        return [
            tr
            for tr in self._tracks.values()
            if tr.time_since_update == 0 and tr.hits >= self.min_hits
        ]

    def active_tracks(self) -> list[Track]:
        return list(self._tracks.values())
