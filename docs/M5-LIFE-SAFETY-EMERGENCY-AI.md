# M5 — Life Safety & Emergency AI

**Status:** Implemented (Sprints 1–6)

M5 adds temporally verified fire, smoke, weapon, fall, and PPE signals plus a unified emergency incident manager.

| Sprint | Scope | Status |
|---|---|---|
| 1 | Flame labels, indoor/outdoor profiles, confidence, multi-frame confirmation, evidence | Done |
| 2 | Smoke density, early warning, sensitivity, persistence, trend | Done |
| 3 | Handgun/rifle/optional knife labels and person-track association | Done |
| 4 | Fall confirmation, immobility escalation, recovery | Done |
| 5 | Zone/shift/role-aware PPE compliance | Done |
| 6 | Emergency correlation, actions, escalation, command center | Done |

## Important inference boundary

The temporal verification and event pipeline are production interfaces, but detector accuracy depends on deployed model weights:

- Generic COCO person weights are not safety-grade fire, smoke, PPE, or weapon models.
- Production deployments must provide custom YOLO-compatible labels such as `fire`, `smoke`, `handgun`, `rifle`, `helmet`, and `safety_vest`.
- PPE absence checks are disabled by default (`ppe_model_enabled=false`) until a PPE-capable model is configured.
- Fall detection currently uses tracked-person geometry and motion. A pose-estimation adapter can replace it behind the same event contract.

## Edge pipeline

```text
Frame → Custom detector labels + person tracks
      → SafetyAnalyzer
         ├─ fire multi-frame confirmation
         ├─ smoke trend/persistence
         ├─ weapon↔person association
         ├─ fall/immobility/recovery state
         └─ PPE zone/shift/role policy
      → snapshot + optional rolling evidence clip
      → /api/v1/events/ingest/
```

Key paths:

- `edge/edge_service/safety/analyzer.py`
- `edge/edge_service/safety/evidence.py`
- `edge/edge_service/pipeline.py`

Environment:

- `ENABLE_SAFETY=true`
- `ENABLE_SAFETY_EVIDENCE=false`
- `SAFETY_EVIDENCE_SECONDS=5`
- `ENABLE_SNAPSHOTS=true`

## Backend

`apps.safety` adds:

- `SafetyProfile`
- `FireEvent`
- `SmokeEvent`
- `WeaponEvent`
- `FallEvent`
- `PPEEvent`
- `EmergencyIncident`
- `EmergencyEventLink`
- `EmergencyAction`
- `EmergencyEscalation`

`SafetyProfile` controls per-camera thresholds, confirmation windows, knife policy, fall timing, PPE requirements, shifts, roles, and enforcement zones.

## Emergency correlation

Safety signals from the same site are grouped over a five-minute window.

Examples:

- Fire + smoke → `emergency`
- Weapon + crowd → `emergency`
- Confirmed fire or weapon → `critical`
- Fall → `high`
- PPE alone remains a compliance event and does not create an emergency

Recommended actions are persisted as requested action records:

- Save evidence
- Start continuous recording
- Notify fire/security/medical response
- Lock relevant access points
- Display in Emergency Command Center

External notification, access-control, and VMS execution remain M6 integrations.

## APIs

- `GET /api/v1/fire-events/`
- `GET /api/v1/smoke-events/`
- `GET /api/v1/weapon-events/`
- `GET /api/v1/fall-events/`
- `GET /api/v1/ppe-events/`
- `GET/POST /api/v1/safety-profiles/`
- `GET /api/v1/safety/summary/`
- `GET /api/v1/emergency-incidents/`
- `POST /api/v1/emergency-incidents/{id}/acknowledge/`
- `POST /api/v1/emergency-incidents/{id}/contain/`
- `POST /api/v1/emergency-incidents/{id}/resolve/`

## Dashboard

Fire · Smoke · Weapons · Falls · PPE · Emergency

## Verification

Backend tests cover typed persistence, fire+smoke correlation, fall recovery, APIs, and incident acknowledgement. Edge tests cover temporal fire/smoke verification, weapon association, fall recovery, and guarded PPE checks.

## Next: M6 Enterprise Operations

Notifications, multi-site operations, executive reporting, SSO, HA, backup/DR, SIEM, ONVIF/VMS, Prometheus/Grafana, and centralized logging.
