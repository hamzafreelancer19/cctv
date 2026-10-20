"""M2 unit tests: zones, tracker, detector factory, event builder, stream health shapes."""

from __future__ import annotations

import numpy as np

from edge_service.events.builder import EventCooldown, build_person_event, build_zone_event
from edge_service.inference import SimulatedYOLODetector, build_event_payload
from edge_service.tracker.iou_tracker import IOUTracker
from edge_service.types import BoundingBox, Detection, Track
from edge_service.yolo.detector import SimulatedDetector, create_detector
from edge_service.zones.engine import ZoneConfig, ZoneEngine, point_in_polygon


def test_simulated_detector_returns_valid_structure():
    detector = SimulatedYOLODetector()
    results = []
    for _ in range(20):
        results.extend(detector.detect())
    assert len(results) >= 0
    if results:
        r = results[0]
        assert r.event_type == "person_detected"
        assert 0 <= r.confidence <= 1


def test_build_event_payload():
    from edge_service.inference import DetectionResult

    det = DetectionResult(
        event_type="person_detected",
        severity="warning",
        confidence=0.85,
        model_name="yolo-sim",
        model_version="0.1.0",
        payload={"track_id": 1},
    )
    event = build_event_payload("cam-uuid", det)
    assert event["camera_id"] == "cam-uuid"
    assert event["event_type"] == "person_detected"
    assert "edge_event_id" in event


def test_point_in_polygon_center():
    poly = [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]
    assert point_in_polygon(0.5, 0.5, poly) is True
    assert point_in_polygon(1.5, 0.5, poly) is False


def test_zone_engine_intrusion():
    zone = ZoneConfig(
        zone_id="z1",
        name="Restricted",
        polygon=[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
        is_restricted=True,
    )
    engine = ZoneEngine([zone], loitering_seconds=100)
    track = Track(
        track_id=7,
        bbox=BoundingBox(10, 10, 50, 50),
        confidence=0.9,
        first_seen_ts=1.0,
        last_seen_ts=1.0,
    )
    events = engine.evaluate([track], frame_w=100, frame_h=100, now=1.0)
    assert any(e.event_type == "intrusion" and e.track_id == 7 for e in events)


def test_zone_engine_loitering():
    zone = ZoneConfig(
        zone_id="z1",
        name="Lobby",
        polygon=[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
        is_restricted=False,
        loitering_seconds=2.0,
    )
    engine = ZoneEngine([zone])
    track = Track(track_id=3, bbox=BoundingBox(10, 10, 40, 40), confidence=0.8, first_seen_ts=0, last_seen_ts=0)
    engine.evaluate([track], 100, 100, now=1.0)
    events = engine.evaluate([track], 100, 100, now=4.0)
    assert any(e.event_type == "loitering" and e.payload.get("activity") == "loitering" for e in events)


def test_zone_engine_exit_and_reenter_loiter():
    zone = ZoneConfig(
        zone_id="z1",
        name="Lobby",
        polygon=[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
        loitering_seconds=2.0,
    )
    engine = ZoneEngine([zone])
    inside = Track(track_id=1, bbox=BoundingBox(10, 10, 40, 40), confidence=0.9, first_seen_ts=0, last_seen_ts=0)
    outside = Track(track_id=1, bbox=BoundingBox(200, 200, 230, 240), confidence=0.9, first_seen_ts=0, last_seen_ts=0)
    engine.evaluate([inside], 100, 100, now=1.0)
    exit_events = engine.evaluate([outside], 100, 100, now=2.0)
    assert any(e.event_type == "zone_exit" for e in exit_events)
    engine.evaluate([inside], 100, 100, now=3.0)
    loiter = engine.evaluate([inside], 100, 100, now=6.0)
    assert any(e.event_type == "loitering" for e in loiter)


def test_iou_tracker_persists_id():
    tracker = IOUTracker(iou_threshold=0.3)
    d1 = [Detection(bbox=BoundingBox(10, 10, 40, 80), confidence=0.9)]
    tracks1 = tracker.update(d1, now=1.0)
    assert len(tracks1) == 1
    tid = tracks1[0].track_id

    d2 = [Detection(bbox=BoundingBox(12, 12, 42, 82), confidence=0.91)]
    tracks2 = tracker.update(d2, now=1.1)
    assert tracks2[0].track_id == tid


def test_create_detector_simulated():
    det = create_detector(backend="simulated")
    assert isinstance(det, SimulatedDetector)
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    # probabilistic; just ensure no crash
    det.detect(frame)


def test_event_cooldown():
    cd = EventCooldown(cooldown_sec=60)
    assert cd.allow("c1", "person_detected", 1) is True
    assert cd.allow("c1", "person_detected", 1) is False
    assert cd.allow("c1", "intrusion", 1) is True


def test_build_person_and_zone_events():
    track = Track(track_id=9, bbox=BoundingBox(1, 2, 30, 60), confidence=0.77)
    person = build_person_event("cam", track, "yolo-sim", "0.2.0")
    assert person["event_type"] == "person_detected"
    assert person["payload"]["track_id"] == 9

    from edge_service.zones.engine import ZoneEvent

    ze = ZoneEvent(
        event_type="intrusion",
        severity="critical",
        track_id=9,
        zone_id="z1",
        zone_name="Server Room",
        confidence=0.9,
        payload={"restricted": True},
    )
    evt = build_zone_event("cam", ze, "yolo-sim", "0.2.0")
    assert evt["event_type"] == "intrusion"
    assert evt["zone_id"] == "z1"
