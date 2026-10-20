"""M5 temporal safety verification over custom-model detections and person tracks."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, time as dtime
from typing import Any

from edge_service.types import BoundingBox, Detection, Track
from edge_service.zones.engine import ZoneConfig, point_in_polygon

FIRE_LABELS = {"fire", "flame"}
SMOKE_LABELS = {"smoke"}
WEAPON_LABELS = {"handgun", "gun", "pistol", "rifle", "knife", "weapon"}
PPE_LABELS = {"helmet", "hardhat", "safety_vest", "vest", "safety_glasses"}


@dataclass
class SafetySignal:
    event_type: str
    severity: str
    confidence: float
    payload: dict[str, Any] = field(default_factory=dict)
    zone_id: str | None = None
    track_id: int | None = None


@dataclass
class _FallState:
    horizontal_since: float | None = None
    immobile_since: float | None = None
    last_center: tuple[float, float] | None = None
    fall_emitted: bool = False
    immobile_emitted: bool = False


DEFAULT_PROFILE: dict[str, Any] = {
    "enabled": True,
    "environment": "indoor",
    "fire_threshold": 0.75,
    "fire_confirmation_frames": 3,
    "smoke_threshold": 0.55,
    "smoke_persistence_seconds": 8.0,
    "smoke_sensitivity": 1.0,
    "weapon_threshold": 0.65,
    "detect_knives": False,
    "fall_confirmation_seconds": 2.0,
    "fall_immobility_seconds": 20.0,
    "ppe_required": ["helmet", "safety_vest"],
    "ppe_model_enabled": False,
    "ppe_contractor_only": False,
    "ppe_shift_start": None,
    "ppe_shift_end": None,
    "ppe_zone_ids": [],
}


class SafetyAnalyzer:
    def __init__(self, profile: dict[str, Any] | None = None):
        self.profile = {**DEFAULT_PROFILE, **(profile or {})}
        self.fire_frames = 0
        self.fire_active = False
        self.smoke_started: float | None = None
        self.smoke_history: deque[float] = deque(maxlen=10)
        self.smoke_early_emitted = False
        self.smoke_persistent_emitted = False
        self.falls: dict[int, _FallState] = {}
        self.last_ppe_check: dict[int, float] = {}

    def set_profile(self, profile: dict[str, Any] | None):
        self.profile = {**DEFAULT_PROFILE, **(profile or {})}

    def analyze(
        self,
        frame: Any,
        detections: list[Detection],
        person_tracks: list[Track],
        timestamp: float,
        zones: list[ZoneConfig] | None = None,
        person_context: dict[int, dict[str, Any]] | None = None,
    ) -> list[SafetySignal]:
        if not self.profile.get("enabled", True):
            return []
        zones = zones or []
        person_context = person_context or {}
        signals: list[SafetySignal] = []
        signals.extend(self._fire(detections, frame, timestamp))
        signals.extend(self._smoke(detections, frame, timestamp))
        signals.extend(self._weapons(detections, person_tracks, person_context))
        signals.extend(self._falls(person_tracks, timestamp, person_context))
        signals.extend(self._ppe(detections, person_tracks, timestamp, zones, person_context))
        return signals

    def _fire(self, detections, frame, timestamp):
        threshold = float(self.profile["fire_threshold"])
        candidates = [
            item
            for item in detections
            if item.class_name.lower() in FIRE_LABELS and item.confidence >= threshold
        ]
        self.fire_frames = self.fire_frames + 1 if candidates else 0
        if not candidates:
            self.fire_active = False
            return []
        required = int(self.profile["fire_confirmation_frames"])
        if self.fire_frames < required or self.fire_active:
            return []
        self.fire_active = True
        best = max(candidates, key=lambda item: item.confidence)
        frame_area = max(1.0, float(frame.shape[0] * frame.shape[1])) if frame is not None else 1.0
        return [
            SafetySignal(
                event_type="fire",
                severity="critical",
                confidence=best.confidence,
                payload={
                    "verified": True,
                    "confirmation_frames": self.fire_frames,
                    "environment": self.profile["environment"],
                    "area_ratio": round(best.bbox.area / frame_area, 4),
                    "bbox": best.bbox.as_xywh(),
                    "duration_seconds": 0,
                },
            )
        ]

    def _smoke(self, detections, frame, timestamp):
        threshold = float(self.profile["smoke_threshold"]) / max(
            0.1, float(self.profile["smoke_sensitivity"])
        )
        candidates = [
            item
            for item in detections
            if item.class_name.lower() in SMOKE_LABELS and item.confidence >= threshold
        ]
        if not candidates:
            self.smoke_started = None
            self.smoke_history.clear()
            self.smoke_early_emitted = False
            self.smoke_persistent_emitted = False
            return []
        best = max(candidates, key=lambda item: item.confidence)
        if self.smoke_started is None:
            self.smoke_started = timestamp
        frame_area = max(1.0, float(frame.shape[0] * frame.shape[1])) if frame is not None else 1.0
        density = min(1.0, best.bbox.area / frame_area)
        previous = sum(self.smoke_history) / len(self.smoke_history) if self.smoke_history else density
        self.smoke_history.append(density)
        trend = "rising" if density > previous * 1.1 else "falling" if density < previous * 0.9 else "stable"
        duration = timestamp - self.smoke_started
        persistent = duration >= float(self.profile["smoke_persistence_seconds"])
        if (not persistent and self.smoke_early_emitted) or (persistent and self.smoke_persistent_emitted):
            return []
        self.smoke_early_emitted = True
        if persistent:
            self.smoke_persistent_emitted = True
        level = "high" if density >= 0.35 else "medium" if density >= 0.15 else "low"
        return [
            SafetySignal(
                event_type="smoke",
                severity="critical" if persistent or level == "high" else "warning",
                confidence=best.confidence,
                payload={
                    "density": round(density, 4),
                    "density_level": level,
                    "trend": trend,
                    "persistent": persistent,
                    "duration_seconds": round(duration, 2),
                    "bbox": best.bbox.as_xywh(),
                },
            )
        ]

    def _weapons(self, detections, tracks, context):
        signals = []
        threshold = float(self.profile["weapon_threshold"])
        for item in detections:
            label = item.class_name.lower()
            if label not in WEAPON_LABELS or item.confidence < threshold:
                continue
            if label == "knife" and not self.profile.get("detect_knives"):
                continue
            track = self._associate(item.bbox, tracks)
            identity = context.get(track.track_id, {}) if track else {}
            signals.append(
                SafetySignal(
                    event_type="weapon",
                    severity="critical",
                    confidence=item.confidence,
                    track_id=track.track_id if track else None,
                    payload={
                        "weapon_type": label,
                        "track_id": track.track_id if track else None,
                        "person_id": identity.get("person_id"),
                        "associated": bool(track),
                        "bbox": item.bbox.as_xywh(),
                    },
                )
            )
        return signals

    def _falls(self, tracks, timestamp, context):
        signals = []
        live = {track.track_id for track in tracks}
        for track in tracks:
            state = self.falls.setdefault(track.track_id, _FallState())
            horizontal = track.bbox.width > track.bbox.height * 1.2
            center = (track.bbox.cx, track.bbox.cy)
            moved = (
                abs(center[0] - state.last_center[0]) + abs(center[1] - state.last_center[1])
                if state.last_center
                else 999
            )
            state.last_center = center
            identity = context.get(track.track_id, {})
            if horizontal:
                state.horizontal_since = state.horizontal_since or timestamp
                if moved < 6:
                    state.immobile_since = state.immobile_since or timestamp
                else:
                    state.immobile_since = timestamp
                duration = timestamp - state.horizontal_since
                if duration >= float(self.profile["fall_confirmation_seconds"]) and not state.fall_emitted:
                    state.fall_emitted = True
                    signals.append(
                        SafetySignal(
                            event_type="fall",
                            severity="critical",
                            confidence=track.confidence,
                            track_id=track.track_id,
                            payload={
                                "track_id": track.track_id,
                                "person_id": identity.get("person_id"),
                                "status": "fallen",
                                "duration_seconds": round(duration, 2),
                                "immobile_seconds": 0,
                                "bbox": track.bbox.as_xywh(),
                            },
                        )
                    )
                immobile = timestamp - state.immobile_since if state.immobile_since else 0
                if (
                    state.fall_emitted
                    and immobile >= float(self.profile["fall_immobility_seconds"])
                    and not state.immobile_emitted
                ):
                    state.immobile_emitted = True
                    signals.append(
                        SafetySignal(
                            event_type="fall",
                            severity="critical",
                            confidence=track.confidence,
                            track_id=track.track_id,
                            payload={
                                "track_id": track.track_id,
                                "person_id": identity.get("person_id"),
                                "status": "immobile",
                                "duration_seconds": round(duration, 2),
                                "immobile_seconds": round(immobile, 2),
                                "bbox": track.bbox.as_xywh(),
                            },
                        )
                    )
            else:
                if state.fall_emitted:
                    signals.append(
                        SafetySignal(
                            event_type="fall_recovery",
                            severity="info",
                            confidence=track.confidence,
                            track_id=track.track_id,
                            payload={
                                "track_id": track.track_id,
                                "person_id": identity.get("person_id"),
                                "status": "recovered",
                            },
                        )
                    )
                self.falls[track.track_id] = _FallState(last_center=center)
        for track_id in list(self.falls):
            if track_id not in live:
                del self.falls[track_id]
        return signals

    def _ppe(self, detections, tracks, timestamp, zones, context):
        if not self.profile.get("ppe_model_enabled"):
            return []
        if not self._in_shift(timestamp):
            return []
        ppe = [item for item in detections if item.class_name.lower() in PPE_LABELS]
        required = list(self.profile.get("ppe_required") or [])
        zone_ids = set(self.profile.get("ppe_zone_ids") or [])
        signals = []
        for track in tracks:
            if timestamp - self.last_ppe_check.get(track.track_id, 0) < 30:
                continue
            identity = context.get(track.track_id, {})
            person_type = identity.get("person_type", "")
            if self.profile.get("ppe_contractor_only") and person_type != "contractor":
                continue
            zone_id = self._track_zone(track, zones, zone_ids)
            if zone_ids and not zone_id:
                continue
            present = set()
            for item in ppe:
                if track.bbox.iou(item.bbox) > 0.01 or self._inside(item.bbox, track.bbox):
                    label = item.class_name.lower()
                    present.add("helmet" if label in {"helmet", "hardhat"} else "safety_vest" if label in {"vest", "safety_vest"} else label)
            missing = [item for item in required if item not in present]
            self.last_ppe_check[track.track_id] = timestamp
            if missing:
                signals.append(
                    SafetySignal(
                        event_type="ppe_violation",
                        severity="warning",
                        confidence=track.confidence,
                        track_id=track.track_id,
                        zone_id=zone_id,
                        payload={
                            "track_id": track.track_id,
                            "person_id": identity.get("person_id"),
                            "person_type": person_type,
                            "required_items": required,
                            "missing_items": missing,
                            "present_items": sorted(present),
                            "bbox": track.bbox.as_xywh(),
                        },
                    )
                )
        return signals

    def _track_zone(self, track, zones, allowed):
        for zone in zones:
            if allowed and zone.zone_id not in allowed:
                continue
            # Bounding boxes are pixel based; zone filtering is finalized by the
            # pipeline, which provides normalized dimensions in track metadata.
            centroid = track.metadata.get("normalized_centroid")
            if centroid and point_in_polygon(centroid[0], centroid[1], zone.polygon):
                return zone.zone_id
        return None

    def _in_shift(self, timestamp):
        start = self._parse_time(self.profile.get("ppe_shift_start"))
        end = self._parse_time(self.profile.get("ppe_shift_end"))
        if not start or not end:
            return True
        current = datetime.fromtimestamp(timestamp).time()
        return start <= current <= end if start <= end else current >= start or current <= end

    @staticmethod
    def _parse_time(value):
        if not value:
            return None
        try:
            h, m, *_ = str(value).split(":")
            return dtime(int(h), int(m))
        except Exception:
            return None

    @staticmethod
    def _associate(bbox: BoundingBox, tracks: list[Track]):
        if not tracks:
            return None
        scored = [(bbox.iou(track.bbox), track) for track in tracks]
        score, track = max(scored, key=lambda pair: pair[0])
        if score > 0:
            return track
        # Weapon boxes may be small and adjacent: use nearest person center.
        track = min(
            tracks,
            key=lambda item: abs(item.bbox.cx - bbox.cx) + abs(item.bbox.cy - bbox.cy),
        )
        distance = abs(track.bbox.cx - bbox.cx) + abs(track.bbox.cy - bbox.cy)
        return track if distance <= max(track.bbox.width, track.bbox.height) else None

    @staticmethod
    def _inside(inner: BoundingBox, outer: BoundingBox):
        return outer.x1 <= inner.cx <= outer.x2 and outer.y1 <= inner.cy <= outer.y2
