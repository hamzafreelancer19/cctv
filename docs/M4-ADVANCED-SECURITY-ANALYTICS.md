# M4 — Advanced Security Analytics

**Status:** Implemented (Sprints 1–6)

Intrusion hardening, loitering, crowd, object left/removed, event correlation, and configurable rule engine.

| Sprint | Scope | Status |
|--------|-------|--------|
| 1 | Multi-zone intrusion, schedules, entry/exit, priority, dwell | Done |
| 2 | Configurable loitering + escalation | Done |
| 3 | Crowd occupancy / density / heatmaps | Done |
| 4 | Object left / removed tracking | Done |
| 5 | Multi-signal risk correlation | Done |
| 6 | Configurable analytics rules + actions | Done |

## Pipeline

```
Person / Object Tracks
        │
   Zone Rules (priority, schedule, direction)
        │
   Crowd Analyzer  +  Object State Tracker
        │
   DetectionEvent ingest
        │
   Specialized tables + Correlation + Rule Engine
        │
   Alerts / Risk Incidents / Dashboard
```

## Backend (`apps.analytics` + Zone extensions)

| Table / Model | Purpose |
|---------------|---------|
| Zone (+ M4 fields) | priority, loiter timers, occupancy, access hours, entry line, cameras M2M |
| AnalyticsRule | Configurable conditions (types, time, zone, require_all) |
| RuleAction | alert / snapshot / recording / notify |
| LoiterEvent | Typed loitering with escalation |
| CrowdStatistic | Occupancy samples + heatmap |
| ObjectEvent | left / removed |
| RiskIncident | Correlated high-risk incidents |
| EventCorrelation | Links DetectionEvents → incidents |

### Key APIs

| Endpoint | Purpose |
|----------|---------|
| `GET/POST /api/v1/zones/` | Zone CRUD (enriched fields) |
| `GET /api/v1/loiter-events/` | Loitering history |
| `GET /api/v1/crowd/` | Crowd samples |
| `GET /api/v1/crowd/summary/` | Live occupancy metrics |
| `GET /api/v1/object-events/` | Left/removed objects |
| `GET /api/v1/risk-incidents/` | Risk dashboard |
| `POST /api/v1/risk-incidents/{id}/{action}/` | acknowledge / resolve |
| `GET/POST /api/v1/rules/` | Analytics rule engine |
| `GET /api/v1/incidents/timeline/` | Mixed incident timeline |

## Edge modules

| Module | Path |
|--------|------|
| Hardened zone engine | `edge/edge_service/zones/engine.py` |
| Crowd analyzer | `edge/edge_service/crowd.py` |
| Object tracker | `edge/edge_service/objects/tracker.py` |
| Pipeline hooks | `edge/edge_service/pipeline.py` |

Env: `LOITERING_SECONDS`, `OBJECT_LEFT_SECONDS`, `EVENT_COOLDOWN_SEC`

## Dashboard

Zones · Crowd · Objects · Risk (sidebar)

## Example rule (seeded)

```
AfterHoursIntrusion
  event: intrusion
  time: 20:00–06:00
  actions: alert, snapshot, recording(stub)
```

## Next

**M5 Safety AI:** fire, smoke, weapon, fall, PPE detection.
