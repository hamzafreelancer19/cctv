"""M4 correlation + configurable rule engine."""

from __future__ import annotations

from datetime import datetime, time, timedelta

from django.db.models import Avg, Count, Max
from django.utils import timezone

from apps.alerts.models import Alert
from apps.events.models import DetectionEvent, EventType, Severity

from .models import (
    AnalyticsRule,
    CrowdStatistic,
    EventCorrelation,
    LoiterEvent,
    ObjectEvent,
    ObjectEventKind,
    RiskIncident,
    RiskLevel,
    RuleAction,
)

RISK_WEIGHTS = {
    EventType.UNKNOWN_PERSON: 2.5,
    EventType.INTRUSION: 3.0,
    EventType.LOITERING: 2.0,
    EventType.ACTIVITY: 1.5,
    EventType.OBJECT_LEFT: 2.0,
    EventType.OBJECT_REMOVED: 2.5,
    EventType.CROWD: 1.5,
    EventType.ZONE_ENTER: 0.5,
    EventType.ZONE_EXIT: 0.3,
}

RISK_LEVEL_FROM_SCORE = (
    (8.0, RiskLevel.CRITICAL),
    (5.0, RiskLevel.HIGH),
    (2.5, RiskLevel.MEDIUM),
    (0.0, RiskLevel.LOW),
)

SEVERITY_FROM_RISK = {
    RiskLevel.CRITICAL: Severity.CRITICAL,
    RiskLevel.HIGH: Severity.CRITICAL,
    RiskLevel.MEDIUM: Severity.WARNING,
    RiskLevel.LOW: Severity.INFO,
}


def _local_time_in_window(now_t: time, start: time | None, end: time | None) -> bool:
    if start is None or end is None:
        return True
    if start <= end:
        return start <= now_t <= end
    # overnight window e.g. 20:00–06:00
    return now_t >= start or now_t <= end


def _score_to_level(score: float) -> str:
    for threshold, level in RISK_LEVEL_FROM_SCORE:
        if score >= threshold:
            return level
    return RiskLevel.LOW


def record_specialized_event(event: DetectionEvent) -> None:
    """Persist typed M4 tables from a DetectionEvent."""
    org = event.organization
    payload = event.payload or {}
    if event.event_type in (EventType.LOITERING, EventType.ACTIVITY) and (
        event.event_type == EventType.LOITERING or payload.get("activity") == "loitering"
    ):
        track_id = payload.get("track_id")
        zone = event.zone
        recent = (
            LoiterEvent.objects.filter(
                organization=org,
                camera=event.camera,
                track_id=track_id,
                zone=zone,
                created_at__gte=timezone.now() - timedelta(minutes=30),
            )
            .order_by("-created_at")
            .first()
        )
        escalation = (recent.escalation_count + 1) if recent else 1
        severity = Severity.CRITICAL if escalation >= 3 else event.severity
        LoiterEvent.objects.create(
            organization=org,
            camera=event.camera,
            zone=zone,
            detection_event=event,
            track_id=track_id,
            dwell_seconds=float(payload.get("dwell_seconds") or 0),
            threshold_seconds=float(payload.get("threshold_seconds") or 0),
            person_type=str(payload.get("person_type") or ""),
            escalation_count=escalation,
            severity=severity,
            payload=payload,
        )
    elif event.event_type == EventType.CROWD:
        CrowdStatistic.objects.create(
            organization=org,
            camera=event.camera,
            zone=event.zone,
            occupancy=int(payload.get("occupancy") or 0),
            max_occupancy=payload.get("max_occupancy"),
            density=float(payload.get("density") or 0),
            over_capacity=bool(payload.get("over_capacity")),
            peak_hour=timezone.localtime(event.created_at).hour,
            heatmap=payload.get("heatmap") or [],
            recorded_at=event.created_at,
        )
    elif event.event_type in (EventType.OBJECT_LEFT, EventType.OBJECT_REMOVED):
        ObjectEvent.objects.create(
            organization=org,
            camera=event.camera,
            zone=event.zone,
            detection_event=event,
            kind=ObjectEventKind.LEFT if event.event_type == EventType.OBJECT_LEFT else ObjectEventKind.REMOVED,
            object_class=str(payload.get("object_class") or "bag"),
            track_id=payload.get("track_id"),
            confidence=event.confidence,
            dwell_seconds=float(payload.get("dwell_seconds") or 0),
            severity=event.severity,
            payload=payload,
        )


def correlate_events(event: DetectionEvent) -> RiskIncident | None:
    """
    Sprint 5 — correlate related events in a time window into a risk incident.
    Example: unknown_person + loitering + intrusion → high risk.
    """
    org = event.organization
    window = timedelta(seconds=180)
    since = event.created_at - window
    related = DetectionEvent.objects.filter(
        camera__site__organization=org,
        created_at__gte=since,
        created_at__lte=event.created_at,
        event_type__in=[
            EventType.UNKNOWN_PERSON,
            EventType.INTRUSION,
            EventType.LOITERING,
            EventType.ACTIVITY,
            EventType.OBJECT_LEFT,
            EventType.OBJECT_REMOVED,
            EventType.CROWD,
            EventType.ZONE_ENTER,
        ],
    ).select_related("camera", "zone")[:40]

    events = list(related) + [event]
    types = {e.event_type for e in events}
    # Heuristic composite: unknown + (loiter|activity) + (intrusion|restricted zone enter)
    has_unknown = EventType.UNKNOWN_PERSON in types
    has_loiter = EventType.LOITERING in types or any(
        e.event_type == EventType.ACTIVITY and (e.payload or {}).get("activity") == "loitering" for e in events
    )
    has_restricted = EventType.INTRUSION in types or any(
        e.event_type == EventType.ZONE_ENTER and (e.payload or {}).get("restricted") for e in events
    )

    score = sum(RISK_WEIGHTS.get(e.event_type, 0.5) for e in events)
    if has_unknown and has_loiter and has_restricted:
        score += 4.0
        title = "High Risk: Unknown + Loitering + Restricted Zone"
    elif has_unknown and (has_loiter or has_restricted):
        score += 2.0
        title = "Elevated Risk: Unknown Person Activity"
    elif len(types) < 2:
        return None
    else:
        title = f"Correlated Incident ({len(types)} signal types)"

    level = _score_to_level(score)
    if level == RiskLevel.LOW and score < 3.0:
        return None

    # Dedup: reuse open incident in same camera within window
    existing = (
        RiskIncident.objects.filter(
            organization=org,
            camera=event.camera,
            status="open",
            created_at__gte=since,
        )
        .order_by("-created_at")
        .first()
    )
    if existing:
        existing.risk_score = max(existing.risk_score, score)
        existing.risk_level = _score_to_level(existing.risk_score)
        existing.summary = f"{existing.summary}\n+ {event.event_type}".strip()
        existing.save(update_fields=["risk_score", "risk_level", "summary", "updated_at"])
        EventCorrelation.objects.get_or_create(incident=existing, event=event, defaults={"weight": RISK_WEIGHTS.get(event.event_type, 1.0)})
        return existing

    incident = RiskIncident.objects.create(
        organization=org,
        site=event.camera.site,
        zone=event.zone,
        camera=event.camera,
        title=title,
        risk_level=level,
        risk_score=round(score, 2),
        summary=f"Correlated {len(events)} events: {', '.join(sorted(types))}",
    )
    for e in events:
        EventCorrelation.objects.get_or_create(
            incident=incident, event=e, defaults={"weight": RISK_WEIGHTS.get(e.event_type, 1.0)}
        )
    Alert.objects.create(
        organization=org,
        event=event,
        title=f"[{level.upper()}] {title}",
        message=incident.summary,
        severity=SEVERITY_FROM_RISK.get(level, Severity.WARNING),
    )
    return incident


def evaluate_analytics_rules(event: DetectionEvent) -> list[RiskIncident]:
    """Sprint 6 — configurable rules with time windows and actions."""
    org = event.organization
    site = event.camera.site
    now_local = timezone.localtime(event.created_at)
    # Prefer site timezone if pytz/zoneinfo available via Django
    try:
        import zoneinfo

        tz = zoneinfo.ZoneInfo(site.timezone)
        now_local = event.created_at.astimezone(tz)
    except Exception:
        pass
    now_t = now_local.time()

    created: list[RiskIncident] = []
    rules = (
        AnalyticsRule.objects.filter(organization=org, is_active=True)
        .prefetch_related("actions")
        .order_by("priority")
    )
    for rule in rules:
        if rule.site_id and rule.site_id != site.id:
            continue
        if rule.zone_id and event.zone_id and rule.zone_id != event.zone_id:
            continue
        if rule.zone_id and not event.zone_id:
            continue
        if event.confidence < rule.min_confidence:
            continue
        if not _local_time_in_window(now_t, rule.time_start, rule.time_end):
            continue

        types = set(rule.event_types or [])
        if not types:
            continue
        if event.event_type not in types and not (
            event.event_type == EventType.ACTIVITY
            and "loitering" in types
            and (event.payload or {}).get("activity") == "loitering"
        ):
            continue

        since = event.created_at - timedelta(seconds=rule.window_seconds)
        window_qs = DetectionEvent.objects.filter(
            camera__site__organization=org,
            created_at__gte=since,
            created_at__lte=event.created_at,
        )
        if rule.zone_id:
            window_qs = window_qs.filter(zone_id=rule.zone_id)
        elif rule.site_id:
            window_qs = window_qs.filter(camera__site_id=rule.site_id)

        seen = set(window_qs.values_list("event_type", flat=True))
        # Map activity+loitering to loitering for matching
        if any(
            e.event_type == EventType.ACTIVITY and (e.payload or {}).get("activity") == "loitering"
            for e in window_qs.filter(event_type=EventType.ACTIVITY)[:20]
        ):
            seen.add(EventType.LOITERING)

        if rule.require_all:
            if not types.issubset(seen | {event.event_type}):
                continue
        elif event.event_type not in types and EventType.LOITERING not in (seen & types):
            # single-type rules fire on matching event
            if not (types & seen):
                continue

        incident = RiskIncident.objects.create(
            organization=org,
            site=site,
            zone=event.zone or rule.zone,
            camera=event.camera,
            rule=rule,
            title=rule.name,
            risk_level=rule.risk_level,
            risk_score=float(RISK_WEIGHTS.get(event.event_type, 1.0) * (2 if rule.require_all else 1)),
            summary=rule.description or f"Rule '{rule.name}' matched on {event.event_type}",
            actions_taken=[],
        )
        EventCorrelation.objects.get_or_create(incident=incident, event=event, defaults={"weight": 1.0})
        actions_log = []
        for action in rule.actions.filter(is_active=True):
            actions_log.append(_execute_action(action, event, incident))
        incident.actions_taken = actions_log
        incident.save(update_fields=["actions_taken", "updated_at"])
        created.append(incident)
    return created


def _execute_action(action: RuleAction, event: DetectionEvent, incident: RiskIncident) -> dict:
    if action.action_type == "alert":
        Alert.objects.create(
            organization=event.organization,
            event=event,
            title=f"Rule: {incident.title}",
            message=incident.summary,
            severity=SEVERITY_FROM_RISK.get(incident.risk_level, Severity.WARNING),
        )
        return {"action": "alert", "status": "created"}
    if action.action_type == "snapshot":
        return {"action": "snapshot", "status": "requested", "path": (event.payload or {}).get("snapshot")}
    if action.action_type == "recording":
        return {"action": "recording", "status": "stub", "note": "Edge recording hook planned"}
    if action.action_type == "notify":
        return {"action": "notify", "status": "stub", "channels": action.config.get("channels", ["email"])}
    return {"action": action.action_type, "status": "unknown"}


def process_m4_ingest(event: DetectionEvent) -> dict:
    """Hook called after DetectionEvent create."""
    record_specialized_event(event)
    incident = correlate_events(event)
    rule_incidents = evaluate_analytics_rules(event)
    return {
        "correlated": bool(incident),
        "incident_id": str(incident.id) if incident else None,
        "rules_matched": len(rule_incidents),
    }


def crowd_summary(organization_id, camera_id=None) -> dict:
    qs = CrowdStatistic.objects.filter(organization_id=organization_id)
    if camera_id:
        qs = qs.filter(camera_id=camera_id)
    latest = qs.order_by("-recorded_at").first()
    day = timezone.now().date()
    today = qs.filter(recorded_at__date=day)
    agg = today.aggregate(avg=Avg("occupancy"), peak=Max("occupancy"), samples=Count("id"))
    peak_hours = (
        today.values("peak_hour").annotate(c=Count("id"), max_occ=Max("occupancy")).order_by("-max_occ")[:5]
    )
    return {
        "current_occupancy": latest.occupancy if latest else 0,
        "max_occupancy_limit": latest.max_occupancy if latest else None,
        "average_occupancy": round(agg["avg"] or 0, 2),
        "maximum_occupancy": agg["peak"] or 0,
        "samples_today": agg["samples"] or 0,
        "over_capacity": bool(latest and latest.over_capacity),
        "density": latest.density if latest else 0,
        "heatmap": latest.heatmap if latest else [],
        "peak_hours": list(peak_hours),
        "recorded_at": latest.recorded_at.isoformat() if latest else None,
    }
