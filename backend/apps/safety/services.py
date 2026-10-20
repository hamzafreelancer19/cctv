"""Typed safety persistence and emergency correlation."""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.alerts.models import Alert
from apps.events.models import DetectionEvent, EventType
from apps.identity.models import Person

from .models import (
    EmergencyAction,
    EmergencyEscalation,
    EmergencyEventLink,
    EmergencyIncident,
    EmergencySeverity,
    FallEvent,
    FireEvent,
    PPEEvent,
    SmokeEvent,
    WeaponEvent,
)

SAFETY_TYPES = {
    EventType.FIRE,
    EventType.SMOKE,
    EventType.WEAPON,
    EventType.FALL,
    EventType.FALL_RECOVERY,
    EventType.PPE_VIOLATION,
}

SIGNAL_WEIGHTS = {
    EventType.FIRE: 6.0,
    EventType.SMOKE: 3.0,
    EventType.WEAPON: 6.0,
    EventType.FALL: 3.5,
    EventType.FALL_RECOVERY: -1.5,
    EventType.PPE_VIOLATION: 1.0,
    EventType.CROWD: 2.0,
}


def _person(event, payload):
    person_id = payload.get("person_id")
    if not person_id:
        return None
    return Person.objects.filter(id=person_id, organization=event.organization).first()


def _base(event, payload):
    return {
        "organization": event.organization,
        "camera": event.camera,
        "zone": event.zone,
        "detection_event": event,
        "confidence": event.confidence,
        "duration_seconds": float(payload.get("duration_seconds") or 0),
        "snapshot_path": str(payload.get("snapshot") or ""),
        "evidence_clip_path": str(payload.get("evidence_clip") or ""),
        "payload": payload,
    }


def persist_safety_event(event: DetectionEvent):
    payload = event.payload or {}
    base = _base(event, payload)
    if event.event_type == EventType.FIRE:
        return FireEvent.objects.create(
            **base,
            environment=str(payload.get("environment") or "indoor"),
            confirmation_frames=int(payload.get("confirmation_frames") or 1),
            flame_area_ratio=float(payload.get("area_ratio") or 0),
            verified=bool(payload.get("verified", True)),
        )
    if event.event_type == EventType.SMOKE:
        density = float(payload.get("density") or 0)
        return SmokeEvent.objects.create(
            **base,
            density=density,
            density_level=str(payload.get("density_level") or "low"),
            trend=str(payload.get("trend") or "stable"),
            persistent=bool(payload.get("persistent")),
        )
    if event.event_type == EventType.WEAPON:
        return WeaponEvent.objects.create(
            **base,
            person=_person(event, payload),
            track_id=payload.get("track_id"),
            weapon_type=str(payload.get("weapon_type") or "unknown"),
            associated=bool(payload.get("associated")),
        )
    if event.event_type == EventType.FALL:
        return FallEvent.objects.create(
            **base,
            person=_person(event, payload),
            track_id=payload.get("track_id"),
            status=str(payload.get("status") or "fallen"),
            immobile_seconds=float(payload.get("immobile_seconds") or 0),
        )
    if event.event_type == EventType.FALL_RECOVERY:
        fall = (
            FallEvent.objects.filter(
                organization=event.organization,
                camera=event.camera,
                track_id=payload.get("track_id"),
                status__in=["fallen", "immobile"],
            )
            .order_by("-created_at")
            .first()
        )
        if fall:
            fall.status = "recovered"
            fall.recovered_at = event.created_at
            fall.save(update_fields=["status", "recovered_at", "updated_at"])
        return fall
    if event.event_type == EventType.PPE_VIOLATION:
        required = payload.get("required_items") or []
        missing = payload.get("missing_items") or []
        return PPEEvent.objects.create(
            **base,
            person=_person(event, payload),
            track_id=payload.get("track_id"),
            person_type=str(payload.get("person_type") or ""),
            required_items=required,
            missing_items=missing,
            compliant=not bool(missing),
        )
    return None


def _incident_title(types) -> str:
    labels = sorted(
        label.replace("_", " ").title()
        for label in types
        if label != EventType.PPE_VIOLATION
    )
    return " / ".join(labels) if labels else "Life Safety"


def _severity(score, types):
    if EventType.FIRE in types and EventType.SMOKE in types:
        return EmergencySeverity.EMERGENCY
    if EventType.WEAPON in types and EventType.CROWD in types:
        return EmergencySeverity.EMERGENCY
    if score >= 9:
        return EmergencySeverity.EMERGENCY
    if score >= 6:
        return EmergencySeverity.CRITICAL
    if score >= 3:
        return EmergencySeverity.HIGH
    return EmergencySeverity.WARNING


def _recommended(types):
    actions = ["save_evidence", "display_emergency_dashboard"]
    if EventType.FIRE in types or EventType.SMOKE in types:
        actions += ["notify_fire_response", "start_continuous_recording"]
    if EventType.WEAPON in types:
        actions += ["notify_security", "lock_relevant_access_points"]
    if EventType.FALL in types:
        actions += ["dispatch_medical_assistance"]
    return list(dict.fromkeys(actions))


@transaction.atomic
def correlate_emergency(event: DetectionEvent):
    """Merge related safety signals at the same site into one open incident."""
    since = event.created_at - timedelta(minutes=5)
    related = list(
        DetectionEvent.objects.filter(
            camera__site=event.camera.site,
            created_at__gte=since,
            created_at__lte=event.created_at,
            event_type__in=list(SAFETY_TYPES | {EventType.CROWD}),
        ).order_by("-created_at")[:50]
    )
    if event not in related:
        related.append(event)
    types = {item.event_type for item in related}
    # Score unique signal types once — repeat frames must not inflate emergencies.
    score = max(0.0, sum(SIGNAL_WEIGHTS.get(signal, 0) for signal in types))

    # PPE alone is a compliance report, not an emergency.
    if types <= {EventType.PPE_VIOLATION}:
        return None

    severity = _severity(score, types)
    title = _incident_title(types)
    summary = f"Correlated life-safety signals: {', '.join(sorted(types))}"
    actions = _recommended(types)
    incident = (
        EmergencyIncident.objects.filter(
            organization=event.organization,
            site=event.camera.site,
            status__in=["open", "acknowledged"],
            created_at__gte=since,
        )
        .order_by("-created_at")
        .first()
    )
    old_severity = incident.severity if incident else None
    if not incident:
        incident = EmergencyIncident.objects.create(
            organization=event.organization,
            site=event.camera.site,
            camera=event.camera,
            zone=event.zone,
            title=title,
            severity=severity,
            score=score,
            summary=summary,
            recommended_actions=actions,
            continuous_recording_requested=severity in ["critical", "emergency"],
            notifications_requested=True,
        )
    else:
        incident.title = title
        incident.score = max(incident.score, score)
        incident.severity = severity
        incident.summary = summary
        incident.recommended_actions = actions
        incident.continuous_recording_requested = severity in ["critical", "emergency"]
        incident.notifications_requested = True
        incident.save()

    for related_event in related:
        EmergencyEventLink.objects.get_or_create(incident=incident, event=related_event)

    if old_severity and old_severity != severity:
        EmergencyEscalation.objects.create(
            incident=incident,
            from_severity=old_severity,
            to_severity=severity,
            reason=f"New signal: {event.event_type}",
        )

    existing_actions = set(incident.actions.values_list("action_type", flat=True))
    for action in incident.recommended_actions:
        if action not in existing_actions:
            EmergencyAction.objects.create(
                incident=incident,
                action_type=action,
                status="requested",
                details={"source_event_id": str(event.id)},
            )

    if not Alert.objects.filter(
        organization=event.organization,
        event=event,
        title__startswith="[LIFE SAFETY]",
    ).exists():
        Alert.objects.create(
            organization=event.organization,
            event=event,
            title=f"[LIFE SAFETY] {event.get_event_type_display()} — {event.camera.name}",
            message=incident.summary,
            severity="critical" if severity in ["critical", "emergency"] else "warning",
        )
    return incident


def process_m5_ingest(event: DetectionEvent):
    if event.event_type not in SAFETY_TYPES and event.event_type != EventType.CROWD:
        return None
    typed = persist_safety_event(event) if event.event_type in SAFETY_TYPES else None
    incident = correlate_emergency(event)
    return {
        "typed_event_id": str(typed.id) if typed else None,
        "incident_id": str(incident.id) if incident else None,
    }
