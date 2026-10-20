import numpy as np

from edge_service.safety.analyzer import SafetyAnalyzer
from edge_service.types import BoundingBox, Detection, Track


def frame():
    return np.zeros((200, 300, 3), dtype=np.uint8)


def detection(label, confidence=0.9, bbox=None):
    return Detection(
        bbox=bbox or BoundingBox(20, 20, 100, 100),
        confidence=confidence,
        class_id=99,
        class_name=label,
    )


def person(track_id=1, bbox=None):
    return Track(
        track_id=track_id,
        bbox=bbox or BoundingBox(10, 10, 110, 190),
        confidence=0.92,
    )


def test_fire_requires_multiple_frames():
    analyzer = SafetyAnalyzer({"fire_threshold": 0.7, "fire_confirmation_frames": 3})
    assert analyzer.analyze(frame(), [detection("fire")], [], 1.0) == []
    assert analyzer.analyze(frame(), [detection("fire")], [], 2.0) == []
    signals = analyzer.analyze(frame(), [detection("fire")], [], 3.0)
    assert len(signals) == 1
    assert signals[0].event_type == "fire"
    assert signals[0].payload["verified"] is True


def test_smoke_early_warning_then_persistent_escalation():
    analyzer = SafetyAnalyzer(
        {"smoke_threshold": 0.5, "smoke_persistence_seconds": 2.0}
    )
    first = analyzer.analyze(frame(), [detection("smoke")], [], 1.0)
    assert first[0].event_type == "smoke"
    assert first[0].payload["persistent"] is False
    persistent = analyzer.analyze(frame(), [detection("smoke")], [], 4.0)
    assert persistent[0].payload["persistent"] is True
    assert persistent[0].severity == "critical"


def test_weapon_associates_to_person_track():
    analyzer = SafetyAnalyzer({"weapon_threshold": 0.5})
    track = person()
    signals = analyzer.analyze(
        frame(),
        [detection("handgun", bbox=BoundingBox(50, 70, 85, 105))],
        [track],
        1.0,
        person_context={1: {"person_id": "known-id", "person_type": "employee"}},
    )
    weapon = next(signal for signal in signals if signal.event_type == "weapon")
    assert weapon.track_id == 1
    assert weapon.payload["person_id"] == "known-id"


def test_fall_confirmation_and_recovery():
    analyzer = SafetyAnalyzer(
        {"fall_confirmation_seconds": 1.0, "fall_immobility_seconds": 10.0}
    )
    fallen = person(bbox=BoundingBox(10, 100, 180, 170))
    assert not any(
        signal.event_type == "fall"
        for signal in analyzer.analyze(frame(), [], [fallen], 1.0)
    )
    confirmed = analyzer.analyze(frame(), [], [fallen], 2.5)
    assert any(signal.event_type == "fall" for signal in confirmed)
    upright = person(bbox=BoundingBox(10, 10, 80, 190))
    recovery = analyzer.analyze(frame(), [], [upright], 3.0)
    assert any(signal.event_type == "fall_recovery" for signal in recovery)


def test_ppe_violation_requires_ppe_capable_profile():
    track = person()
    disabled = SafetyAnalyzer({"ppe_model_enabled": False})
    assert disabled.analyze(frame(), [], [track], 31.0) == []

    enabled = SafetyAnalyzer(
        {
            "ppe_model_enabled": True,
            "ppe_required": ["helmet", "safety_vest"],
        }
    )
    signals = enabled.analyze(
        frame(),
        [detection("helmet", bbox=BoundingBox(30, 10, 70, 50))],
        [track],
        31.0,
    )
    ppe = next(signal for signal in signals if signal.event_type == "ppe_violation")
    assert ppe.payload["missing_items"] == ["safety_vest"]
