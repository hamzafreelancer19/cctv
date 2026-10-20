"""M4 Crowd analytics — occupancy, density, simple heatmap cells."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from edge_service.types import Track
from edge_service.zones.engine import ZoneConfig, point_in_polygon


@dataclass
class CrowdSnapshot:
    occupancy: int
    max_occupancy: int | None
    density: float
    over_capacity: bool
    heatmap: list[dict[str, float]] = field(default_factory=list)
    zone_id: str | None = None
    zone_name: str | None = None


class CrowdAnalyzer:
    def __init__(self, grid: int = 8):
        self.grid = grid
        self._last_emit: dict[str, float] = {}

    def analyze(
        self,
        tracks: list[Track],
        frame_w: int,
        frame_h: int,
        zones: list[ZoneConfig],
        now: float,
        emit_interval: float = 5.0,
    ) -> list[tuple[CrowdSnapshot, bool]]:
        """Return list of (snapshot, should_emit_event)."""
        results: list[tuple[CrowdSnapshot, bool]] = []
        target_zones = zones or [
            ZoneConfig(zone_id="full", name="Full Frame", polygon=[[0, 0], [1, 0], [1, 1], [0, 1]])
        ]
        for zone in target_zones:
            centroids = []
            for track in tracks:
                nx, ny = track.bbox.normalized_centroid(frame_w, frame_h)
                if point_in_polygon(nx, ny, zone.polygon):
                    centroids.append((nx, ny))
            occ = len(centroids)
            # Approximate density by people / polygon bbox area
            xs = [p[0] for p in zone.polygon] or [0, 1]
            ys = [p[1] for p in zone.polygon] or [0, 1]
            area = max(1e-6, (max(xs) - min(xs)) * (max(ys) - min(ys)))
            density = occ / area
            over = bool(zone.max_occupancy is not None and occ > zone.max_occupancy)
            heatmap = self._heatmap(centroids)
            snap = CrowdSnapshot(
                occupancy=occ,
                max_occupancy=zone.max_occupancy,
                density=round(density, 3),
                over_capacity=over,
                heatmap=heatmap,
                zone_id=zone.zone_id,
                zone_name=zone.name,
            )
            key = zone.zone_id
            last = self._last_emit.get(key, 0.0)
            should = (now - last) >= emit_interval and (occ > 0 or over)
            if should:
                self._last_emit[key] = now
            results.append((snap, should or over))
        return results

    def _heatmap(self, centroids: list[tuple[float, float]]) -> list[dict[str, float]]:
        g = self.grid
        cells: dict[tuple[int, int], int] = {}
        for x, y in centroids:
            cx = min(g - 1, max(0, int(x * g)))
            cy = min(g - 1, max(0, int(y * g)))
            cells[(cx, cy)] = cells.get((cx, cy), 0) + 1
        return [{"x": cx / g, "y": cy / g, "w": float(w)} for (cx, cy), w in cells.items()]
