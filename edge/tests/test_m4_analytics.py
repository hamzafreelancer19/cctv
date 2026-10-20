"""M4 edge unit tests — crowd + object left/removed."""

from __future__ import annotations

from edge_service.crowd import CrowdAnalyzer
from edge_service.objects.tracker import ObjectStateTracker
from edge_service.types import BoundingBox, Detection, Track
from edge_service.zones.engine import ZoneConfig, in_access_window


def test_after_hours_window_overnight():
    # 20:00–06:00: 22:00 is outside working hours → False for in_access_window
    # Use a fixed timestamp — we only check parse logic with synthetic times via function
    assert in_access_window.__doc__  # smoke
    # midday should be inside 09-18
    import datetime as dt

    midday = dt.datetime(2026, 7, 17, 12, 0, 0).timestamp()
    assert in_access_window(midday, "09:00", "18:00") is True
    night = dt.datetime(2026, 7, 17, 22, 0, 0).timestamp()
    assert in_access_window(night, "09:00", "18:00") is False
    # overnight working? unusual — access 20-06 means night is "in window"
    assert in_access_window(night, "20:00", "06:00") is True


def test_crowd_over_capacity():
    zone = ZoneConfig(
        zone_id="z1",
        name="Lobby",
        polygon=[[0, 0], [1, 0], [1, 1], [0, 1]],
        max_occupancy=1,
    )
    tracks = [
        Track(track_id=1, bbox=BoundingBox(10, 10, 30, 50), confidence=0.9),
        Track(track_id=2, bbox=BoundingBox(40, 10, 60, 50), confidence=0.9),
    ]
    analyzer = CrowdAnalyzer()
    results = analyzer.analyze(tracks, 100, 100, [zone], now=1.0, emit_interval=0)
    snap, should = results[0]
    assert snap.occupancy == 2
    assert snap.over_capacity is True
    assert should is True


def test_object_left_behind():
    tracker = ObjectStateTracker(left_seconds=2.0, max_miss=1.0)
    det = Detection(bbox=BoundingBox(70, 70, 90, 90), confidence=0.9, class_id=24, class_name="bag")
    tracker.update([det], now=1.0)
    events = tracker.update([det], now=4.0)
    assert any(e.event_type == "object_left" for e in events)
    # disappear
    removed = tracker.update([], now=6.0)
    assert any(e.event_type == "object_removed" for e in removed)
