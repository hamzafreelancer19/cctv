"""M4 Zone engine — multi-zone intrusion, schedules, entry/exit, dwell, priority."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, time as dtime
from typing import Any

from edge_service.types import Track

PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def point_in_polygon(x: float, y: float, polygon: list[list[float]]) -> bool:
    """Ray casting; polygon points are normalized [x,y] in 0..1 space."""
    if not polygon or len(polygon) < 3:
        return False
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i][0], polygon[i][1]
        xj, yj = polygon[j][0], polygon[j][1]
        intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi)
        if intersect:
            inside = not inside
        j = i
    return inside


def cross_product_side(px: float, py: float, line: list[list[float]]) -> float:
    """Signed side of point relative to directed line A→B. >0 left, <0 right."""
    if not line or len(line) < 2:
        return 0.0
    (x1, y1), (x2, y2) = line[0], line[1]
    return (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)


def parse_hhmm(value: str | None) -> dtime | None:
    if not value:
        return None
    try:
        parts = value.split(":")
        return dtime(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
    except Exception:
        return None


def in_access_window(now_ts: float, access_start: str | None, access_end: str | None) -> bool:
    """True if local wall-clock is within working hours. Missing bounds = always open."""
    start = parse_hhmm(access_start)
    end = parse_hhmm(access_end)
    if start is None or end is None:
        return True
    local = datetime.fromtimestamp(now_ts).time()
    if start <= end:
        return start <= local <= end
    return local >= start or local <= end


@dataclass
class ZoneConfig:
    zone_id: str
    name: str
    polygon: list[list[float]]
    is_restricted: bool = False
    loitering_seconds: float = 120.0
    visitor_loitering_seconds: float = 60.0
    ignore_employees: bool = False
    priority: str = "medium"
    max_occupancy: int | None = None
    access_start: str | None = None
    access_end: str | None = None
    after_hours_restricted: bool = True
    entry_line: list[list[float]] = field(default_factory=list)


@dataclass
class ZoneEvent:
    event_type: str
    severity: str
    track_id: int
    zone_id: str
    zone_name: str
    confidence: float
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class _PresenceState:
    entered_at: float
    last_side: float = 0.0
    loiter_emitted: bool = False
    loiter_count: int = 0
    last_centroid: tuple[float, float] = (0.0, 0.0)


class ZoneEngine:
    """Evaluate tracks against camera zones with enter/exit/dwell/schedule."""

    def __init__(self, zones: list[ZoneConfig] | None = None, loitering_seconds: float = 120.0):
        self.zones = sorted(zones or [], key=lambda z: PRIORITY_RANK.get(z.priority, 2))
        self.loitering_seconds = loitering_seconds
        # track_id -> zone_id -> PresenceState
        self._presence: dict[int, dict[str, _PresenceState]] = {}

    def set_zones(self, zones: list[ZoneConfig]):
        self.zones = sorted(zones, key=lambda z: PRIORITY_RANK.get(z.priority, 2))

    def evaluate(
        self,
        tracks: list[Track],
        frame_w: int,
        frame_h: int,
        now: float | None = None,
        person_types: dict[int, str] | None = None,
    ) -> list[ZoneEvent]:
        now = now if now is not None else time.time()
        person_types = person_types or {}
        events: list[ZoneEvent] = []
        live_track_ids = {t.track_id for t in tracks}
        active_keys: set[tuple[int, str]] = set()

        for track in tracks:
            nx, ny = track.bbox.normalized_centroid(frame_w, frame_h)
            ptype = person_types.get(track.track_id, "")

            for zone in self.zones:
                inside = point_in_polygon(nx, ny, zone.polygon)
                key = (track.track_id, zone.zone_id)
                presence_map = self._presence.setdefault(track.track_id, {})
                state = presence_map.get(zone.zone_id)

                if not inside:
                    if state is not None:
                        events.append(
                            ZoneEvent(
                                event_type="zone_exit",
                                severity="info",
                                track_id=track.track_id,
                                zone_id=zone.zone_id,
                                zone_name=zone.name,
                                confidence=track.confidence,
                                payload={
                                    "dwell_seconds": round(now - state.entered_at, 2),
                                    "centroid": [nx, ny],
                                    "bbox": track.bbox.as_xywh(),
                                    "priority": zone.priority,
                                    "direction": self._exit_direction(state, nx, ny, zone),
                                },
                            )
                        )
                        del presence_map[zone.zone_id]
                    continue

                active_keys.add(key)
                after_hours = not in_access_window(now, zone.access_start, zone.access_end)
                effectively_restricted = zone.is_restricted or (
                    after_hours and zone.after_hours_restricted
                )

                if state is None:
                    side = cross_product_side(nx, ny, zone.entry_line) if zone.entry_line else 0.0
                    presence_map[zone.zone_id] = _PresenceState(
                        entered_at=now, last_side=side, last_centroid=(nx, ny)
                    )
                    direction = "entry" if side >= 0 else "exit_crossing"
                    events.append(
                        ZoneEvent(
                            event_type="zone_enter",
                            severity="info",
                            track_id=track.track_id,
                            zone_id=zone.zone_id,
                            zone_name=zone.name,
                            confidence=track.confidence,
                            payload={
                                "centroid": [nx, ny],
                                "bbox": track.bbox.as_xywh(),
                                "priority": zone.priority,
                                "restricted": effectively_restricted,
                                "after_hours": after_hours,
                                "direction": direction,
                            },
                        )
                    )
                    if effectively_restricted:
                        sev = "critical" if zone.priority in ("critical", "high") or after_hours else "warning"
                        events.append(
                            ZoneEvent(
                                event_type="intrusion",
                                severity=sev,
                                track_id=track.track_id,
                                zone_id=zone.zone_id,
                                zone_name=zone.name,
                                confidence=track.confidence,
                                payload={
                                    "centroid": [nx, ny],
                                    "bbox": track.bbox.as_xywh(),
                                    "restricted": True,
                                    "after_hours": after_hours,
                                    "priority": zone.priority,
                                    "direction": direction,
                                },
                            )
                        )
                    continue

                # update dwell / direction side
                state.last_centroid = (nx, ny)
                if zone.entry_line:
                    state.last_side = cross_product_side(nx, ny, zone.entry_line)

                if zone.ignore_employees and ptype == "employee":
                    continue

                threshold = zone.loitering_seconds or self.loitering_seconds
                if ptype == "visitor" and zone.visitor_loitering_seconds:
                    threshold = zone.visitor_loitering_seconds

                dwell = now - state.entered_at
                if dwell >= threshold and not state.loiter_emitted:
                    state.loiter_emitted = True
                    state.loiter_count += 1
                    sev = "critical" if state.loiter_count >= 2 or zone.priority == "critical" else "warning"
                    events.append(
                        ZoneEvent(
                            event_type="loitering",
                            severity=sev,
                            track_id=track.track_id,
                            zone_id=zone.zone_id,
                            zone_name=zone.name,
                            confidence=track.confidence,
                            payload={
                                "activity": "loitering",
                                "dwell_seconds": round(dwell, 2),
                                "threshold_seconds": threshold,
                                "centroid": [nx, ny],
                                "bbox": track.bbox.as_xywh(),
                                "priority": zone.priority,
                                "person_type": ptype,
                                "escalation_count": state.loiter_count,
                            },
                        )
                    )
                elif dwell >= threshold * (1 + state.loiter_count) and state.loiter_emitted:
                    # Repeated violation escalation
                    state.loiter_count += 1
                    events.append(
                        ZoneEvent(
                            event_type="loitering",
                            severity="critical",
                            track_id=track.track_id,
                            zone_id=zone.zone_id,
                            zone_name=zone.name,
                            confidence=track.confidence,
                            payload={
                                "activity": "loitering",
                                "dwell_seconds": round(dwell, 2),
                                "threshold_seconds": threshold,
                                "escalation_count": state.loiter_count,
                                "priority": zone.priority,
                                "person_type": ptype,
                                "centroid": [nx, ny],
                                "bbox": track.bbox.as_xywh(),
                            },
                        )
                    )

        # Cleanup tracks that disappeared entirely
        for tid in list(self._presence.keys()):
            if tid not in live_track_ids:
                del self._presence[tid]
            elif not self._presence[tid]:
                del self._presence[tid]

        return events

    def occupancy(self, zone_id: str) -> int:
        return sum(1 for zones in self._presence.values() if zone_id in zones)

    @staticmethod
    def _exit_direction(state: _PresenceState, nx: float, ny: float, zone: ZoneConfig) -> str:
        if not zone.entry_line:
            return "unknown"
        side = cross_product_side(nx, ny, zone.entry_line)
        if state.last_side == 0:
            return "unknown"
        if state.last_side > 0 and side <= 0:
            return "exit"
        if state.last_side < 0 and side >= 0:
            return "entry"
        return "unknown"
