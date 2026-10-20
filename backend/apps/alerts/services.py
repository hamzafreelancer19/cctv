SEVERITY_RANK = {"info": 0, "warning": 1, "critical": 2}


def evaluate_alert_rules(event):
    from .models import Alert, AlertRule

    org = event.organization
    rules = AlertRule.objects.filter(organization=org, is_active=True, event_type=event.event_type)
    for rule in rules:
        if SEVERITY_RANK.get(event.severity, 0) < SEVERITY_RANK.get(rule.min_severity, 0):
            continue
        if event.confidence < rule.min_confidence:
            continue
        Alert.objects.create(
            organization=org,
            event=event,
            rule=rule,
            # Camera name belongs in location meta — not in the title (looks like a person name).
            title=event.get_event_type_display(),
            message=(
                f"Detection on camera “{event.camera.name}” at {event.camera.site.name} "
                f"with confidence {event.confidence:.2f}"
            ),
            severity=event.severity,
        )
