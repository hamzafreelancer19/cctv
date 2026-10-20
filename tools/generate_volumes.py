#!/usr/bin/env python3
"""Generate enterprise documentation volume markdown sources."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "volumes"

HEADER = """---
volume: {vol}
title: {title}
status: draft
---

# {title}

> **SentinelVision AI — Enterprise Documentation Suite**
> Status legend: Implemented | Planned | Future

"""


def write(name: str, content: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Generated {path}")


def vol01_prd() -> str:
    return HEADER.format(vol="01", title="Product Requirements Document") + """
## 1. Document Control

| Field | Value |
|-------|-------|
| Document ID | DOC-PRD-001 |
| Version | 1.0.0 |
| Status | Approved for phased delivery |

## 2. Executive Summary

SentinelVision AI transforms CCTV infrastructure into an intelligent security and activity monitoring platform using hybrid deployment: AI inference at the customer edge, centralized control plane for operations, reporting, and governance.

### 2.1 Current MVP (M0/M1) — Implemented

- Multi-tenant Django REST API with JWT authentication
- Organization, site, zone, camera, edge device registry
- Simulated edge person-detection event ingestion
- Dashboard summary, camera inventory, event review, alert acknowledgement
- Docker Compose local stack and basic CI

### 2.2 Target Platform — Planned/Future

- Production YOLO, tracking, InsightFace, threat detection modules
- Visitor management, attendance, reports, notifications
- Object storage, Celery jobs, Kubernetes production deployment
- Enterprise SSO, audit automation, biometric consent workflows

## 3. Business Goals

| ID | Goal | KPI | Target |
|----|------|-----|--------|
| BR-01 | Reduce incident response time | Mean time to acknowledge critical alert | < 2 min |
| BR-02 | Improve threat detection quality | Intrusion/weapon true positive rate | >= 92% |
| BR-03 | Automate attendance | Manual reconciliation hours/week | -80% |
| BR-04 | Visitor compliance | Pre-registered check-in accuracy | >= 98% |
| BR-05 | Platform reliability | Control plane uptime | 99.9% |
| BR-06 | Tenant growth | Active sites per customer | >= 3 |
| BR-07 | Privacy compliance | Biometric consent coverage | 100% |

## 4. Product Vision

Every camera becomes an intelligent sensor protecting people, assets, and operations with privacy-respecting AI that security teams can trust.

## 5. Product Scope

### 5.1 In Scope

| Area | Status |
|------|--------|
| Multi-tenant org/site/zone management | Implemented |
| Camera and edge device registry | Implemented |
| Event ingestion and review queue | Implemented |
| Alert rules and acknowledgement | Partial — rules create alerts; notifications Planned |
| Web dashboard operations UI | Implemented (core screens) |
| Simulated edge inference | Implemented |
| Face recognition and attendance | Planned |
| Weapon/fire/smoke detection | Future |
| Native mobile apps | Future |

### 5.2 Out of Scope (MVP)

- Full VMS/NVR replacement
- Continuous cloud video archive
- Automated law enforcement dispatch
- Custom model training portal (Future)

## 6. User Personas

| Persona | Role | Primary Goals |
|---------|------|---------------|
| Sarah | Security Manager | Threat response, incident audit |
| Ahmed | Facility Admin | Camera config, uptime, user admin |
| Priya | HR Manager | Attendance, visitor compliance |
| James | Edge Technician | Edge install, diagnostics |
| Maria | Executive | Risk dashboards, compliance |

## 7. User Stories

| ID | Story | Priority | Status |
|----|-------|----------|--------|
| US-01 | Real-time intrusion alerts | P0 | Planned |
| US-02 | Review events with evidence | P0 | Partial |
| US-03 | Unknown person in restricted zone | P0 | Planned |
| US-04 | Weapon/fire/smoke severity alerts | P0 | Future |
| US-05 | Register cameras to sites/zones | P0 | Implemented |
| US-06 | RBAC for configuration changes | P0 | Implemented |
| US-07 | Edge device health monitoring | P1 | Implemented |
| US-08 | Automated attendance | P1 | Planned |
| US-09 | Visitor pre-registration | P1 | Planned |
| US-10 | Biometric consent before enrollment | P0 | Planned |
| US-11 | Weekly incident reports | P1 | Planned |
| US-12 | Immutable audit logs | P0 | Partial — model exists, auto logging Planned |

## 8. Functional Requirements

### 8.1 Camera Management (FR-CAM)

| ID | Requirement | Status |
|----|-------------|--------|
| FR-CAM-01 | Register camera with RTSP URL, site, zone | Implemented |
| FR-CAM-02 | ONVIF discovery | Planned |
| FR-CAM-03 | Camera online/offline status from edge heartbeat | Implemented |
| FR-CAM-04 | Assign AI modules per camera | Partial — field exists |
| FR-CAM-05 | Configure detection zone polygons | Implemented (data model) |

### 8.2 Dashboard (FR-DASH)

| ID | Requirement | Status |
|----|-------------|--------|
| FR-DASH-01 | Overview metrics | Implemented |
| FR-DASH-02 | Event review queue with filters | Partial |
| FR-DASH-03 | Live camera status grid | Planned |
| FR-DASH-04 | Role-based navigation | Partial |

### 8.3 Alerts & Notifications (FR-ALERT)

| ID | Requirement | Status |
|----|-------------|--------|
| FR-ALERT-01 | Configurable alert rules | Implemented |
| FR-ALERT-02 | Severity levels info/warning/critical | Implemented |
| FR-ALERT-03 | Email/SMS/push notifications | Planned |
| FR-ALERT-04 | Acknowledgement workflow | Implemented |

### 8.4 Reports (FR-RPT)

| ID | Requirement | Status |
|----|-------------|--------|
| FR-RPT-01 | Incident summary export PDF/CSV | Planned |
| FR-RPT-02 | Attendance report | Planned |
| FR-RPT-03 | Visitor log report | Planned |
| FR-RPT-04 | Audit log export | Planned |

### 8.5 Mobile (FR-MOB)

| ID | Requirement | Status |
|----|-------------|--------|
| FR-MOB-01 | Responsive web for alerts | Implemented |
| FR-MOB-02 | PWA push notifications | Planned |
| FR-MOB-03 | Native iOS/Android apps | Future |

## 9. Non-Functional Requirements

| ID | Category | Requirement | Target | Status |
|----|----------|-------------|--------|--------|
| NFR-01 | Performance | Event ingest latency p95 | < 3s | Planned measurement |
| NFR-02 | Performance | Dashboard load | < 2s | Planned measurement |
| NFR-03 | Scalability | Cameras per edge node | 16 | Target |
| NFR-04 | Availability | Control plane uptime | 99.9% | Future |
| NFR-05 | Security | TLS in transit | 1.2+ | Planned production |
| NFR-06 | Security | AES at rest | Required | Planned |
| NFR-07 | Privacy | Biometric consent mandatory | 100% | Planned |
| NFR-08 | Retention | Event metadata default | 90 days | Planned enforcement |
| NFR-09 | Accessibility | WCAG 2.1 AA | Target | Future |

## 10. AI Modules Overview

| Module | Status | Phase |
|--------|--------|-------|
| Multi-person tracking | Planned | M2 |
| Face recognition | Planned | M3 |
| Unknown person detection | Planned | M3 |
| Intrusion detection | Planned | M2 |
| Activity recognition | Future | M4 |
| Fire/smoke detection | Future | M4 |
| Weapon detection | Future | M4 |
| Attendance | Planned | M3 |
| Visitor management | Planned | M3 |
| Vehicle detection | Future | M5 |
| License plate recognition | Future | M5 |

## 11. Acceptance Criteria

### 11.1 M0/M1 Foundation — Implemented

- JWT login and tenant-scoped APIs operational
- Camera/site CRUD with RBAC enforced on writes
- Edge heartbeat and event ingest functional
- Dashboard displays summary, cameras, events, alerts
- Docker Compose stack starts successfully
- CI runs backend, edge, frontend, and documentation builds

### 11.2 M2 Core AI — Planned

- One RTSP stream connected at edge
- YOLO person detection with tracking IDs
- Zone-based intrusion events generated
- Operator confirms event and acknowledges alert end-to-end

## 12. Known Gaps (Remediation Required)

| Gap | Impact | Remediation |
|-----|--------|-------------|
| Audit auto-logging not wired | Compliance gap | Implement log_audit callers |
| Global edge_event_id lookup | Tenant isolation risk | Scope idempotency per organization |
| Cross-site zone assignment possible | Data integrity risk | Add serializer validation |
| Fallback EDGE_API_KEY without device binding | Security risk | Remove or bind to bootstrap device |
| Notification dispatch absent | Operational gap | Add Celery notification service |

## 13. Roadmap

| Phase | Timeline | Deliverables |
|-------|----------|--------------|
| M0/M1 | Complete | Foundation, simulated pipeline |
| M2 | Weeks 4-10 | RTSP, YOLO, intrusion, alerts |
| M3 | Weeks 11-14 | Face, attendance, visitors |
| M4 | Weeks 15-18 | Threat modules, reports |
| M5 | Weeks 19-24 | Enterprise HA, SSO, analytics |

## 14. Traceability

See `docs/traceability-matrix.csv` for BR/FR/NFR to UC/API/DB/TEST mappings.
"""


def vol02_srs() -> str:
    return HEADER.format(vol="02", title="Software Requirements Specification") + """
## 1. System Overview

SentinelVision AI comprises an edge inference worker, Django REST control plane, React dashboard, PostgreSQL datastore, and planned async/observability services.

### 1.1 Actors

| Actor | Description |
|-------|-------------|
| SecurityOperator | Monitors alerts and reviews events |
| FacilityAdmin | Configures cameras, sites, users |
| HROfficer | Manages attendance and visitors |
| EdgeService | Automated edge worker posting heartbeats/events |
| SystemAuditor | Reviews audit and compliance exports |
| PlatformAdmin | Operates control plane infrastructure |

## 2. Use Cases

| ID | Use Case | Primary Actor | Status |
|----|----------|---------------|--------|
| UC-AUTH-01 | Authenticate with JWT | All users | Implemented |
| UC-CAM-01 | Register camera | FacilityAdmin | Implemented |
| UC-EDGE-01 | Edge heartbeat registration | EdgeService | Implemented |
| UC-EVT-01 | Ingest detection event | EdgeService | Implemented |
| UC-EVT-02 | Review detection event | SecurityOperator | Implemented |
| UC-ALERT-01 | Acknowledge alert | SecurityOperator | Implemented |
| UC-ALERT-02 | Configure alert rule | FacilityAdmin | Implemented |
| UC-ATT-01 | Record attendance via face | EdgeService | Planned |
| UC-VIS-01 | Pre-register visitor | HROfficer | Planned |
| UC-RPT-01 | Export incident report | SystemAuditor | Planned |

### UC-EVT-01 Ingest Detection Event

**Preconditions:** Edge device authenticated; camera active.

**Main flow:**
1. Edge samples inference result.
2. Edge POSTs event payload to `/api/v1/events/ingest/`.
3. API validates camera ownership/site binding.
4. API persists DetectionEvent.
5. API evaluates alert rules and creates Alert records when matched.

**Alternate flows:**
- A1: Duplicate `edge_event_id` returns existing event (200).
- A2: Invalid camera returns 404.
- A3: Camera outside edge site returns 403.

**Postconditions:** Event stored; optional alert created.

### UC-EVT-02 Review Detection Event

**Preconditions:** Operator authenticated with Operator+ role.

**Main flow:**
1. Operator opens event review queue.
2. Operator selects pending event.
3. Operator marks confirmed or false positive.
4. System records reviewer and timestamp.

## 3. UML Use Case Diagram

```mermaid
flowchart LR
  subgraph actors [Actors]
    Operator[SecurityOperator]
    Admin[FacilityAdmin]
    Edge[EdgeService]
    HR[HROfficer]
  end
  subgraph system [SentinelVision]
    UC1[ManageCameras]
    UC2[IngestEvents]
    UC3[ReviewEvents]
    UC4[ManageAlerts]
    UC5[ManageVisitors]
  end
  Admin --> UC1
  Edge --> UC2
  Operator --> UC3
  Operator --> UC4
  HR --> UC5
```

## 4. Activity Diagram — Event Processing

1. Edge captures frame
2. Detector produces candidates
3. Module router evaluates zones/rules
4. Event payload assembled
5. HTTP POST with retry
6. API validation
7. Persist event
8. Evaluate alert rules
9. Dashboard refresh

## 5. Sequence Diagram — Event Ingestion

```mermaid
sequenceDiagram
  participant Edge
  participant API
  participant DB
  participant Rules as AlertRules
  Edge->>API: POST /events/ingest
  API->>DB: Validate camera
  API->>DB: Insert DetectionEvent
  API->>Rules: evaluate_alert_rules
  Rules->>DB: Insert Alert optional
  API-->>Edge: 201 Created
```

## 6. State Diagram — Alert Lifecycle

| State | Description |
|-------|-------------|
| open | Created, awaiting operator action |
| acknowledged | Operator acknowledged |
| resolved | Incident closed |
| dismissed | False alarm or non-actionable |

Transitions: open→acknowledged (operator), acknowledged→resolved (operator), open→dismissed (operator/admin).

## 7. Business Rules

| ID | Rule |
|----|------|
| BR-TEN-01 | All user queries must be scoped to member organizations |
| BR-RBAC-01 | Viewer cannot mutate configuration |
| BR-EDGE-01 | Edge may ingest only for cameras on its site |
| BR-ALERT-01 | Alert severity must be >= rule min severity |
| BR-ALERT-02 | Event confidence must be >= rule min confidence |
| BR-BIO-01 | Face enrollment requires consent record (Planned) |
| BR-RET-01 | Evidence retention defaults to 30 days (Planned enforcement) |

## 8. Validation Rules

| Entity | Field | Validation |
|--------|-------|------------|
| Camera | name | Required, unique per site |
| Camera | rtsp_url | Valid URL format |
| Zone | polygon_json | Array of normalized [x,y] pairs |
| DetectionEvent | confidence | 0.0–1.0 |
| AlertRule | min_confidence | 0.0–1.0 |
| EdgeDevice | api_key | One-time display on create |

## 9. Error Handling

| Code | Condition | Response |
|------|-----------|----------|
| 400 | Serializer validation failure | DRF validation errors |
| 401 | Missing/invalid JWT or edge key | Authentication failed |
| 403 | Role or site mismatch | Permission denied |
| 404 | Resource not found | Not found |
| 409 | Planned idempotency conflict | Future standardized envelope |

**Target error envelope (Planned):**

```json
{"error": {"code": "VALIDATION_ERROR", "message": "...", "details": {}}}
```

## 10. Workflow Specifications

### 10.1 Human Review Workflow

Pending → Confirmed | False Positive | Escalated

Escalated events require supervisor review (Planned).

### 10.2 Edge Offline Workflow

1. Heartbeat missed beyond threshold
2. Edge marked offline (Planned automated rule)
3. Cameras at site marked degraded
4. Operator notification (Planned)

## 11. Security Requirements

- JWT access token 15 minutes; refresh 7 days
- Edge API keys stored hashed (SHA-256)
- Tenant isolation on all list/detail endpoints
- Planned: rate limiting, key rotation, constant-time compare

## 12. Traceability

Each UC maps to FR IDs in Volume 1 and API IDs in Volume 5.
"""


def vol03_design() -> str:
    return HEADER.format(vol="03", title="System Design Document") + """
## 1. Architecture Overview

Hybrid architecture: inference at customer edge; centralized control plane for metadata, UI, reporting, and governance.

### 1.1 Current State (Implemented)

| Component | Technology | Role |
|-----------|------------|------|
| ControlPlaneAPI | Django 5 + DRF | Auth, tenancy, CRUD, ingest |
| Dashboard | React 18 + Vite | Operations UI |
| Database | PostgreSQL / SQLite | Relational metadata |
| EdgeWorker | Python service | Simulated detection + HTTP delivery |
| LocalDeploy | Docker Compose | Dev/staging stack |

### 1.2 Target State (Planned)

| Component | Technology | Role |
|-----------|------------|------|
| ObjectStorage | S3-compatible | Evidence clips |
| TaskQueue | Celery + Redis | Notifications, reports, retention |
| Ingress | Nginx | TLS termination, routing |
| Orchestration | Kubernetes | Production HA |
| Observability | Prometheus/Grafana/ELK | Metrics and logs |

## 2. High-Level Architecture

```mermaid
flowchart LR
  subgraph edgeSite [CustomerSite]
    Cameras[IPCameras] --> EdgeAI[EdgeAIService]
    EdgeAI --> Buffer[EncryptedEventBuffer]
  end
  Buffer -->|HTTPS| API[DjangoRESTAPI]
  Web[ReactDashboard] --> API
  API --> PG[(PostgreSQL)]
  API --> Store[ObjectStorage]
  API --> Queue[CeleryRedis]
  Queue --> Notify[NotificationProviders]
```

## 3. Low-Level Architecture — Control Plane

### 3.1 Django Apps

| App | Responsibility |
|-----|----------------|
| tenancy | Organizations, memberships, roles |
| sites | Sites and zones |
| cameras | Cameras, edge devices, edge auth |
| events | Detection events, ingest, review |
| alerts | Rules and alert lifecycle |
| audit | Audit log model and listing |

### 3.2 Request Path

Client → CORS → SecurityMiddleware → Auth → TenantQuerysetMixin → Serializer → DB

## 4. Edge AI Architecture

### 4.1 Current Pipeline (Implemented)

```
Timer -> SimulatedYOLODetector -> build_event_payload -> ControlPlaneClient.ingest_event
Parallel: heartbeat loop every N seconds
```

### 4.2 Target Pipeline (Planned)

```
RTSP -> FrameSampler -> YOLODetector -> Tracker -> FaceModule -> ZoneRouter -> EventBuilder -> LocalQueue -> HTTPS
```

| Stage | Technology |
|-------|------------|
| Stream ingest | OpenCV / GStreamer |
| Detection | Ultralytics YOLO |
| Tracking | ByteTrack / DeepSORT |
| Face | InsightFace |
| Buffer | Encrypted local disk queue |

## 5. Microservices Evolution

| Stage | Architecture |
|-------|--------------|
| M0/M1 | Modular monolith + edge worker |
| M3 | Extract notification-service |
| M4 | Extract report-service |
| M5 | Optional inference-coordinator service |

**Principle:** Extract services only after boundaries stabilize; avoid premature microservices.

## 6. Cloud Architecture

| Tier | Components |
|------|------------|
| Public | CDN/static dashboard, WAF, LB |
| Application | Django API pods, Celery workers |
| Data | PostgreSQL HA, Redis, object storage |
| Security | Secrets manager, KMS, VPC private subnets |

## 7. Deployment Architecture

| Environment | Purpose | Stack |
|-------------|---------|-------|
| Local | Developer | Docker Compose |
| Staging | Integration | Compose or K8s |
| Production | Customer | Kubernetes + managed DB |

## 8. Docker

Current Compose services: db, backend, frontend, edge.

## 9. Kubernetes (Planned)

- Deployments: api, worker, frontend, edge (customer cluster)
- HPA on api/worker by CPU and queue depth
- Ingress with cert-manager TLS

## 10. Redis & Celery (Planned)

| Queue | Purpose |
|-------|---------|
| notifications | Email/SMS/push dispatch |
| reports | Scheduled PDF/CSV generation |
| retention | Metadata and evidence cleanup |

## 11. Nginx & Load Balancer

- Terminate TLS
- Route `/api/` to Django
- Serve static dashboard
- Rate limit edge ingest endpoints (Planned)

## 12. Monitoring & Logging

| Signal | Tool | Status |
|--------|------|--------|
| API health | `/api/v1/health/` | Implemented |
| Metrics | Prometheus | Planned |
| Dashboards | Grafana | Planned |
| Logs | ELK / OpenSearch | Planned |
| Tracing | OpenTelemetry | Future |

## 13. Capacity Planning

| Edge Node | Cameras | GPU |
|-----------|---------|-----|
| Small | 4-8 | Jetson Orin Nano |
| Medium | 8-12 | RTX 3060 |
| Large | 12-16 | RTX 4070+ |

## 14. Security Zones

| Zone | Trust |
|------|-------|
| Camera LAN | Internal, no outbound internet |
| Edge | Outbound HTTPS only |
| Control Plane | Private subnets, public via LB |

## 15. Migration Stages

1. Harden MVP tenant validation and audit logging
2. Add Redis/Celery and object storage
3. Deploy production YOLO pipeline
4. Introduce biometric and visitor modules
5. Migrate to Kubernetes with HA database
"""


def vol04_database() -> str:
    tables = [
        ("Organization", "Implemented", "tenancy_organization", "Top-level tenant partition"),
        ("UserMembership", "Implemented", "tenancy_usermembership", "Links Django user to org with role"),
        ("Site", "Implemented", "sites_site", "Physical or logical facility under organization"),
        ("Zone", "Implemented", "sites_zone", "Polygon region for rule evaluation"),
        ("Camera", "Implemented", "cameras_camera", "Registered camera stream and module config"),
        ("EdgeDevice", "Implemented", "cameras_edgedevice", "Edge worker registration and API key hash"),
        ("DetectionEvent", "Implemented", "events_detectionevent", "AI inference result metadata"),
        ("AlertRule", "Implemented", "alerts_alertrule", "Rule for automatic alert creation"),
        ("Alert", "Implemented", "alerts_alert", "Operator notification record"),
        ("AuditLog", "Partial", "audit_auditlog", "Configuration and security audit trail"),
        ("BiometricConsent", "Planned", "identity_biometricconsent", "Consent before face enrollment"),
        ("PersonProfile", "Planned", "identity_personprofile", "Employee/visitor identity record"),
        ("FaceEmbedding", "Planned", "identity_faceembedding", "Vector embedding reference"),
        ("VisitorRegistration", "Planned", "visitor_registration", "Pre-registered visitor record"),
        ("AttendanceRecord", "Planned", "attendance_record", "Clock-in/out events"),
        ("EvidenceArtifact", "Planned", "evidence_artifact", "Snapshot/clip metadata in object storage"),
        ("NotificationDelivery", "Planned", "notifications_delivery", "Outbound alert delivery status"),
        ("ModelRegistry", "Planned", "ai_modelregistry", "Deployed model versions per module"),
    ]
    rows = "\n".join(
        f"| DB-{name} | {name} | {status} | `{table}` | {purpose} |"
        for name, status, table, purpose in tables
    )
    return HEADER.format(vol="04", title="Database Design") + f"""
## 1. Overview

PostgreSQL is the primary datastore. Local development may use SQLite. All tenant-owned entities include organization scoping directly or via foreign-key relationships.

## 2. Entity Summary

| ID | Entity | Status | Table | Purpose |
|----|--------|--------|-------|---------|
{rows}

## 3. Implemented Tables — Detailed Specifications

### DB-Organization

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| name | VARCHAR(255) | NOT NULL | |
| slug | SLUG | UNIQUE | |
| settings | JSONB | DEFAULT {{}} | Retention, timezone defaults |
| is_active | BOOLEAN | DEFAULT true | |
| created_at | TIMESTAMPTZ | auto | |
| updated_at | TIMESTAMPTZ | auto | |

**Indexes:** unique(slug)

### DB-Camera

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| site_id | UUID | FK sites_site | CASCADE |
| zone_id | UUID | FK sites_zone, NULL | SET NULL |
| name | VARCHAR(255) | NOT NULL | unique with site |
| rtsp_url | VARCHAR(512) | | |
| status | VARCHAR(20) | | online/offline/error/maintenance |
| enabled_modules | JSONB | | AI modules list |
| last_seen_at | TIMESTAMPTZ | NULL | |
| metadata | JSONB | | |
| is_active | BOOLEAN | DEFAULT true | |

**Indexes:** unique(site_id, name)

### DB-DetectionEvent

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| camera_id | UUID | FK cameras_camera | |
| zone_id | UUID | FK sites_zone, NULL | |
| event_type | VARCHAR(32) | NOT NULL | |
| severity | VARCHAR(16) | | info/warning/critical |
| confidence | FLOAT | | 0.0-1.0 |
| model_name | VARCHAR(128) | | |
| model_version | VARCHAR(64) | | |
| payload | JSONB | | bbox, track_id, etc. |
| review_status | VARCHAR(20) | | pending/confirmed/false_positive/escalated |
| reviewed_by_id | INT | FK auth_user, NULL | |
| reviewed_at | TIMESTAMPTZ | NULL | |
| edge_event_id | VARCHAR(128) | INDEX | Idempotency key |
| created_at | TIMESTAMPTZ | INDEX DESC | |

**Indexes:** (camera_id, event_type), (-created_at)

**Planned index:** (organization_id, created_at) via denormalized org FK or camera join materialized view.

### DB-EdgeDevice

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| api_key_hash | VARCHAR(128) | NOT NULL | SHA-256 hex |
| api_key_prefix | VARCHAR(8) | | Display prefix only |
| last_seen_at | TIMESTAMPTZ | | heartbeat |
| version | VARCHAR(64) | | edge software version |

## 4. Planned Tables

### DB-BiometricConsent

| Column | Type | Notes |
|--------|------|-------|
| person_profile_id | UUID FK | |
| consent_type | VARCHAR | enrollment/retention |
| granted_at | TIMESTAMPTZ | |
| revoked_at | TIMESTAMPTZ NULL | |
| evidence_document_url | TEXT | optional |

### DB-EvidenceArtifact

| Column | Type | Notes |
|--------|------|-------|
| event_id | UUID FK | |
| storage_key | TEXT | S3 object key |
| media_type | VARCHAR | image/mp4 |
| retention_until | TIMESTAMPTZ | |

## 5. Relationships

```
Organization 1--* Site 1--* Camera
Organization 1--* UserMembership *--1 User
Site 1--* Zone
Site 1--* EdgeDevice
Camera 1--* DetectionEvent
DetectionEvent 1--* Alert
Organization 1--* AlertRule
```

## 6. ER Diagram

```mermaid
erDiagram
  Organization ||--o{{ Site : has
  Organization ||--o{{ UserMembership : has
  Site ||--o{{ Camera : has
  Site ||--o{{ Zone : has
  Site ||--o{{ EdgeDevice : has
  Camera ||--o{{ DetectionEvent : generates
  DetectionEvent ||--o{{ Alert : triggers
  Organization ||--o{{ AlertRule : defines
```

## 7. Tenancy Rules

- Every read query filtered by user's organization memberships
- Edge device may access only its site's cameras
- Planned DB constraints preventing cross-site zone assignment

## 8. Migration Strategy

| Phase | Action |
|-------|--------|
| M0 | Initial migrations for core 10 tables |
| M2 | Add evidence_artifact, model_registry |
| M3 | Add identity and visitor tables |
| M4 | Add notification_delivery, retention jobs |
| All | Backward-compatible additive migrations; no destructive changes without migration window |

## 9. Data Integrity Remediation

| Issue | Remediation Migration |
|-------|----------------------|
| Global edge_event_id uniqueness | Composite unique (organization_id, edge_event_id) |
| Zone/site mismatch | CHECK via trigger or app validation + DB constraint |
| Alert/event org mismatch | FK validation through event.camera.site.organization |
"""


def vol05_api() -> str:
    endpoints = [
        ("API-HEALTH", "GET", "/api/v1/health/", "Public", "None", "Health check", "Implemented"),
        ("API-AUTH-TOKEN", "POST", "/api/v1/auth/token/", "Public", "None", "Obtain JWT pair", "Implemented"),
        ("API-AUTH-REFRESH", "POST", "/api/v1/auth/token/refresh/", "Public", "Refresh token", "Rotate access token", "Implemented"),
        ("API-ORG-LIST", "GET", "/api/v1/organizations/", "JWT", "Authenticated member", "List organizations", "Implemented"),
        ("API-MEMBERSHIP-ME", "GET", "/api/v1/memberships/me/", "JWT", "Authenticated", "Current memberships", "Implemented"),
        ("API-DASH-SUMMARY", "GET", "/api/v1/dashboard/summary/", "JWT", "Authenticated", "Overview metrics", "Implemented"),
        ("API-SITE-LIST", "GET/POST", "/api/v1/sites/", "JWT", "Member / Admin+ create", "Site CRUD list/create", "Implemented"),
        ("API-SITE-DETAIL", "GET/PATCH/DELETE", "/api/v1/sites/{id}/", "JWT", "Member / Admin+", "Site detail", "Implemented"),
        ("API-ZONE-LIST", "GET/POST", "/api/v1/zones/", "JWT", "Member / Admin+ create", "Zone CRUD", "Implemented"),
        ("API-CAM-LIST", "GET/POST", "/api/v1/cameras/", "JWT", "Member / Admin+ create", "Camera CRUD", "Implemented"),
        ("API-CAM-DETAIL", "GET/PATCH/DELETE", "/api/v1/cameras/{id}/", "JWT", "Member / Admin+", "Camera detail", "Implemented"),
        ("API-EDGE-DEV-LIST", "GET/POST", "/api/v1/edge-devices/", "JWT", "Member / Admin+ create", "Register edge device", "Implemented"),
        ("API-EDGE-HEARTBEAT", "POST", "/api/v1/edge/heartbeat/", "EdgeKey", "Edge device", "Heartbeat", "Implemented"),
        ("API-EDGE-CAM-LIST", "GET", "/api/v1/edge/cameras/", "EdgeKey", "Edge device", "Site camera list", "Implemented"),
        ("API-EVT-LIST", "GET", "/api/v1/events/", "JWT", "Member", "List detection events", "Implemented"),
        ("API-EVT-INGEST", "POST", "/api/v1/events/ingest/", "EdgeKey", "Edge device", "Ingest event", "Implemented"),
        ("API-EVT-REVIEW", "GET/PATCH", "/api/v1/events/{id}/review/", "JWT", "Operator+", "Review event", "Implemented"),
        ("API-ALERT-RULE-LIST", "GET/POST", "/api/v1/alert-rules/", "JWT", "Member / Admin+ create", "Alert rules", "Implemented"),
        ("API-ALERT-LIST", "GET", "/api/v1/alerts/", "JWT", "Member", "List alerts", "Implemented"),
        ("API-ALERT-ACK", "PATCH", "/api/v1/alerts/{id}/acknowledge/", "JWT", "Operator+", "Update alert status", "Implemented"),
        ("API-AUDIT-LIST", "GET", "/api/v1/audit-logs/", "JWT", "Member", "List audit logs", "Partial"),
        ("API-SCHEMA", "GET", "/api/schema/", "Public", "None", "OpenAPI schema", "Implemented"),
        ("API-DOCS", "GET", "/api/docs/", "Public", "None", "Swagger UI", "Implemented"),
        ("API-ATT-LIST", "GET", "/api/v1/attendance/", "JWT", "HR+", "Attendance records", "Planned"),
        ("API-VIS-LIST", "GET/POST", "/api/v1/visitors/", "JWT", "HR+", "Visitor management", "Planned"),
        ("API-RPT-EXPORT", "POST", "/api/v1/reports/export/", "JWT", "Admin+", "Generate report", "Planned"),
    ]
    rows = "\n".join(
        f"| {eid} | {method} | `{path}` | {auth} | {perm} | {desc} | {status} |"
        for eid, method, path, auth, perm, desc, status in endpoints
    )
    return HEADER.format(vol="05", title="REST API Documentation") + f"""
## 1. API Strategy

- Base path: `/api/v1/`
- Format: JSON, UTF-8, ISO 8601 UTC timestamps
- IDs: UUID in responses
- Pagination: page-number (Implemented); cursor-based (Planned)
- Schema: OpenAPI 3 via drf-spectacular at `/api/schema/`

## 2. Authentication

| Method | Header | Usage |
|--------|--------|-------|
| JWT | Authorization: Bearer `<access>` | User sessions |
| Edge API Key | X-Edge-API-Key: `<key>` | Edge heartbeat and ingest |

## 3. Endpoint Catalog

| ID | Method | Path | Auth | Permissions | Description | Status |
|----|--------|------|------|-------------|-------------|--------|
{rows}

## 4. Endpoint Detail — API-EVT-INGEST

**POST** `/api/v1/events/ingest/`

**Authentication:** Edge API Key

**Request body:**

```json
{{
  "camera_id": "uuid",
  "event_type": "person_detected",
  "severity": "warning",
  "confidence": 0.87,
  "model_name": "yolo-sim",
  "model_version": "0.1.0",
  "payload": {{"track_id": 1, "bbox": [100,100,200,300]}},
  "zone_id": "uuid",
  "edge_event_id": "evt-001"
}}
```

**Validation:**
- camera_id required, must exist and be active
- event_type must be valid enum
- confidence 0.0–1.0
- edge device must belong to same site as camera

**Responses:**
- 201 Created — new event
- 200 OK — duplicate edge_event_id
- 403 Forbidden — site mismatch
- 404 Not Found — camera missing

## 5. Endpoint Detail — API-AUTH-TOKEN

**POST** `/api/v1/auth/token/`

```json
{{"username": "admin", "password": "admin123"}}
```

**Response:**

```json
{{"access": "<jwt>", "refresh": "<jwt>"}}
```

## 6. Permissions Matrix

| Endpoint Group | Owner | Admin | Operator | Viewer |
|----------------|-------|-------|----------|--------|
| Configuration CRUD | Yes | Yes | No | No |
| Event review | Yes | Yes | Yes | No |
| Alert acknowledge | Yes | Yes | Yes | No |
| Read lists | Yes | Yes | Yes | Yes |

## 7. Error Codes

| HTTP | Meaning |
|------|---------|
| 400 | Validation error |
| 401 | Authentication required/failed |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 429 | Rate limit exceeded (Planned) |
| 500 | Internal server error |

## 8. OpenAPI

Generated from Django via drf-spectacular. CI validates schema generation.

## 9. Planned API Enhancements

- Standardized error envelope on all endpoints
- Cursor pagination for events and alerts
- Webhook subscriptions for alert delivery
- Bulk event export for investigations
"""


def vol06_ai() -> str:
    modules = [
        ("AI-FACE", "Face Recognition", "InsightFace", "Planned", "Identify enrolled persons"),
        ("AI-UNKNOWN", "Unknown Person Detection", "InsightFace + threshold", "Planned", "Flag non-enrolled faces"),
        ("AI-TRACK", "Multi-Person Tracking", "YOLO + ByteTrack", "Planned", "Maintain track IDs"),
        ("AI-INTR", "Intrusion Detection", "YOLO + zone rules", "Planned", "Restricted zone entry"),
        ("AI-ACT", "Activity Recognition", "YOLO-Pose", "Future", "Loitering, fall, fight"),
        ("AI-FIRE", "Fire Detection", "Custom YOLO", "Future", "Visual flame cues"),
        ("AI-SMOKE", "Smoke Detection", "Custom YOLO", "Future", "Visual smoke cues"),
        ("AI-WEAPON", "Weapon Detection", "Custom YOLO", "Future", "Firearms/knives"),
        ("AI-ATT", "Attendance", "Face + rules", "Planned", "Clock-in/out"),
        ("AI-VIS", "Visitor Management", "Face + registry", "Planned", "Match pre-registered visitors"),
        ("AI-VEH", "Vehicle Detection", "YOLO", "Future", "Vehicle class detection"),
        ("AI-LPR", "License Plate Recognition", "OCR + detector", "Future", "Plate text extraction"),
    ]
    rows = "\n".join(f"| {mid} | {name} | {model} | {status} | {desc} |" for mid, name, model, status, desc in modules)
    return HEADER.format(vol="06", title="AI Design Document") + f"""
## 1. AI Platform Overview

Edge performs stream ingestion and inference; control plane stores metadata, alerts, and evidence references.

**Current state:** SimulatedYOLODetector produces randomized person_detected events for pipeline validation.

## 2. Module Catalog

| ID | Module | Model | Status | Description |
|----|--------|-------|--------|-------------|
{rows}

## 3. Shared Pipeline

```
RTSP -> FrameSampler -> Detector -> Tracker -> ModuleRouter -> EventBuilder -> LocalQueue -> HTTPS
```

## 4. Module Template

Each module specification includes:
- Input/output contract
- Dataset requirements and licensing
- Model selection criteria
- Confidence thresholds
- Training and evaluation metrics
- Inference flow
- GPU optimization notes
- Versioning and rollback
- Privacy and bias controls

## 5. AI-FACE — Face Recognition

| Attribute | Value |
|-----------|-------|
| Status | Planned |
| Model | InsightFace (buffalo_l or production equivalent) |
| Input | Face crop 112x112+ |
| Output | person_id, confidence, embedding |
| Threshold | 0.75 default; review below 0.85 |
| GPU | Batch inference every N frames |
| Privacy | Requires BiometricConsent record |
| Metrics | TAR@FAR 1e-3 on validation set |

**Inference flow:**
1. YOLO person detection
2. Face landmark detection
3. Embedding extraction
4. Nearest neighbor against gallery
5. Emit face_recognized or unknown_person

## 6. AI-INTR — Intrusion Detection

| Attribute | Value |
|-----------|-------|
| Status | Planned |
| Input | Track centroid + zone polygon |
| Rule | Person enters restricted zone during active schedule |
| Output | intrusion event, severity warning/critical |
| Threshold | detection confidence >= 0.6 |

## 7. AI-WEAPON — Weapon Detection

| Attribute | Value |
|-----------|-------|
| Status | Future |
| Model | Custom YOLO trained on weapon datasets |
| Output | weapon event, critical severity |
| Threshold | 0.70 minimum before alert |
| Human review | Mandatory before escalation |

## 8. AI-ATT — Attendance

| Attribute | Value |
|-----------|-------|
| Status | Planned |
| Input | face_recognized at entry camera |
| Business rules | One check-in per person per day before cutoff |
| Output | attendance record linked to person profile |

## 9. Dataset Governance

| Requirement | Policy |
|-------------|--------|
| Licensing | Commercial-use approved datasets only |
| PII | Anonymize training exports |
| Bias | Evaluate across age/gender/skin tone buckets |
| Retention | Training snapshots deleted after model promotion |

## 10. Model Versioning

| Field | Storage |
|-------|---------|
| model_name | DetectionEvent.model_name |
| model_version | DetectionEvent.model_version |
| registry | Planned ai_modelregistry table |
| rollback | Edge OTA package pin to previous version |

## 11. GPU Optimization

- FP16 inference where supported
- Frame skipping adaptive to GPU load
- Batch face embedding extraction
- Limit concurrent RTSP decodes to hardware capacity

## 12. Performance Metrics

| Module | Precision Target | Recall Target | FPS Target |
|--------|------------------|---------------|------------|
| Person detection | 0.90 | 0.88 | 15+ @1080p |
| Face recognition | 0.95 | 0.90 | 10+ |
| Intrusion | 0.92 | 0.90 | N/A rule-based |
| Weapon | 0.85 | 0.80 | 10+ |

## 13. Current Simulation

SimulatedYOLODetector emits person_detected with random confidence and bbox for integration testing only. Not for production security decisions.
"""


def vol07_ui() -> str:
    screens = [
        ("UI-LOGIN", "Login", "Implemented", "JWT authentication entry"),
        ("UI-DASH", "Dashboard Overview", "Implemented", "Summary metric cards"),
        ("UI-CAM", "Camera Management", "Partial", "Read-only inventory list"),
        ("UI-LIVE", "Live View", "Planned", "Low-latency stream grid"),
        ("UI-EVT", "Event Review", "Partial", "Review queue with confirm/false+"),
        ("UI-ALERT", "Alerts", "Partial", "Alert cards with acknowledge"),
        ("UI-RPT", "Reports", "Planned", "Export and schedule reports"),
        ("UI-ATT", "Attendance", "Planned", "Daily attendance dashboard"),
        ("UI-VIS", "Visitor Management", "Planned", "Pre-register and check-in"),
        ("UI-USR", "User Management", "Planned", "Membership and role admin"),
        ("UI-SET", "Settings", "Planned", "Org settings, retention, modules"),
        ("UI-EDGE", "Edge Health", "Planned", "Device status and diagnostics"),
    ]
    rows = "\n".join(f"| {sid} | {name} | {status} | {desc} |" for sid, name, status, desc in screens)
    return HEADER.format(vol="07", title="UI/UX Specification") + f"""
## 1. Design Principles

- Security-first dark operations theme
- Responsive layout for desktop and mobile browsers
- Clear severity signaling for alerts and events
- Minimize alert fatigue via prioritization and filters
- WCAG 2.1 AA compliance target

## 2. Information Architecture

```
Login -> App Shell
  Overview
  Cameras
  Events
  Alerts
  Reports (Planned)
  Attendance (Planned)
  Visitors (Planned)
  Users (Planned)
  Settings (Planned)
```

## 3. Screen Catalog

| ID | Screen | Status | Description |
|----|--------|--------|-------------|
{rows}

## 4. UI-LOGIN

**Purpose:** Authenticate operator and establish JWT session.

**Components:** username field, password field, submit button, error banner, demo hint.

**States:** idle, loading, error, success redirect.

**Wireframe (ASCII):**

```
+-----------------------------+
|      SentinelVision AI      |
|  [ username            ]    |
|  [ password            ]    |
|  [ Sign in ]                |
+-----------------------------+
```

## 5. UI-DASH

**Metrics:** cameras online/total, events today, pending review, open/critical alerts, edge online/total.

**Interaction:** read-only cards; auto-refresh Planned.

## 6. UI-EVT

**Table columns:** time, type, camera, site, severity, confidence, status, actions.

**Actions:** Confirm, False Positive (Operator+).

**Planned:** filters, pagination controls, evidence thumbnail preview.

## 7. Component Library

| Component | Usage |
|-----------|-------|
| MetricCard | Dashboard KPIs |
| DataTable | Cameras, events |
| AlertCard | Alerts list |
| Badge | status/severity |
| SidebarNav | Primary navigation |
| ErrorBanner | API failures |

## 8. Navigation Flow

Login success -> Overview -> Events/Alerts for investigation -> Acknowledge alert -> Optional review confirmation.

## 9. Responsive Behavior

- Desktop: persistent sidebar
- Mobile: stacked sidebar/nav wrap; tables horizontally scrollable

## 10. Accessibility

- Keyboard navigable form controls
- Color contrast >= 4.5:1 for text
- Planned: focus indicators, ARIA labels on tables/buttons

## 11. PWA

Manifest present; service worker and push notifications Planned.
"""


def vol08_devops() -> str:
    return HEADER.format(vol="08", title="DevOps and Deployment") + """
## 1. Environments

| Environment | Purpose | Status |
|-------------|---------|--------|
| Local | Developer workstation | Implemented |
| CI | Automated validation | Implemented |
| Staging | Pre-production | Planned |
| Production | Customer-facing | Planned |

## 2. CI/CD — GitHub Actions

Current pipeline jobs:
- backend: migrate + pytest
- edge: pytest
- frontend: lint + build
- prd/docs: documentation build

**Planned gates:** coverage thresholds, security scan, container scan, staging deploy.

## 3. Docker

| Image | Base | Purpose |
|-------|------|---------|
| backend | python:3.12-slim | Django API |
| frontend | node:20-alpine + nginx | Dashboard |
| edge | python:3.12-slim | Edge worker |

## 4. Docker Compose

Services: db, backend, frontend, edge with healthchecks and persistent postgres volume.

## 5. Kubernetes (Planned)

- Helm chart with values per environment
- Separate namespaces for staging/production
- Secrets via external secrets operator

## 6. Nginx

- Serve frontend static assets
- Proxy `/api/` to backend
- Planned: TLS termination, rate limits, WAF integration

## 7. SSL/TLS

- Local dev: HTTP
- Production: TLS 1.2+ with auto-renewed certificates

## 8. Redis & Celery (Planned)

Worker deployment for notifications, reports, retention cleanup.

## 9. Monitoring

| Component | Tool | Status |
|-----------|------|--------|
| Metrics | Prometheus | Planned |
| Dashboards | Grafana | Planned |
| Logs | ELK | Planned |
| Uptime | Health checks | Partial |

## 10. Backup & DR

| Asset | RPO | RTO | Method |
|-------|-----|-----|--------|
| PostgreSQL | 15 min | 1 hr | Managed backups + PITR |
| Object storage | 1 hr | 2 hr | Cross-region replication |
| Config/secrets | 24 hr | 4 hr | Git + vault restore |

## 11. Security Hardening

- Non-root containers
- Secret rotation policy
- Network policies in Kubernetes
- Dependabot and bandit in CI (Planned)

## 12. Runbooks

| Scenario | Action |
|----------|--------|
| API unhealthy | Check DB connectivity, restart pods |
| Edge offline | Verify outbound HTTPS, API key, RTSP source |
| Ingest backlog | Scale API replicas, inspect edge queue |
| DB failover | Promote replica, update connection string |
"""


def vol09_testing() -> str:
    tests = [
        ("TEST-API-001", "Health endpoint returns healthy", "Implemented", "FR-DASH-01"),
        ("TEST-API-002", "JWT login returns tokens", "Implemented", "UC-AUTH-01"),
        ("TEST-API-003", "Tenant camera isolation", "Implemented", "BR-TEN-01"),
        ("TEST-API-004", "Event ingest creates event", "Implemented", "UC-EVT-01"),
        ("TEST-API-005", "Duplicate edge_event_id idempotent", "Implemented", "UC-EVT-01"),
        ("TEST-API-006", "Dashboard summary metrics", "Implemented", "FR-DASH-01"),
        ("TEST-EDGE-001", "Simulated detector structure", "Implemented", "AI-TRACK"),
        ("TEST-EDGE-002", "Event payload builder", "Implemented", "API-EVT-INGEST"),
        ("TEST-UI-001", "API base defaults to /api/v1", "Implemented", "UI-DASH"),
        ("TEST-API-007", "RBAC denies viewer config write", "Planned", "FR-CAM-01"),
        ("TEST-API-008", "Cross-tenant ingest forbidden", "Planned", "BR-EDGE-01"),
        ("TEST-E2E-001", "Login to alert acknowledgement", "Planned", "UC-ALERT-01"),
        ("TEST-AI-001", "YOLO precision on validation set", "Planned", "AI-FACE"),
        ("TEST-PERF-001", "Ingest 100 events/sec soak", "Planned", "NFR-01"),
        ("TEST-SEC-001", "OWASP API top 10 scan", "Planned", "NFR-05"),
    ]
    rows = "\n".join(f"| {tid} | {name} | {status} | {ref} |" for tid, name, status, ref in tests)
    return HEADER.format(vol="09", title="Testing Documentation") + f"""
## 1. Test Strategy

Follow the test pyramid: unit -> integration/API -> E2E -> performance/security/UAT.

## 2. Current Baseline

| Suite | Count | Status |
|-------|-------|--------|
| Backend API tests | 5 | Implemented |
| Edge tests | 2 | Implemented |
| Frontend tests | 1 | Implemented |

Coverage target for core backend: >= 80% (Planned enforcement).

## 3. Test Environments

| Env | Data | Usage |
|-----|------|-------|
| Local SQLite/Postgres | seed_dev_data | Developer |
| CI ephemeral | migrations + factories | PR validation |
| Staging | anonymized | Integration/E2E |

## 4. Test Case Catalog

| ID | Test | Status | Requirement Ref |
|----|------|--------|-------------------|
{rows}

## 5. Unit Testing

- Django models, serializers, permissions, alert rule evaluation
- Edge inference helpers and payload builder

## 6. Integration/API Testing

- DRF APIClient with JWT and edge headers
- Tenant isolation across all list endpoints (Planned expansion)

## 7. E2E Testing (Planned)

Playwright flows: login, dashboard load, event review, alert acknowledgement.

## 8. AI Validation (Planned)

- Fixed benchmark clips per module
- Precision/recall/F1 reporting
- False positive rate monitoring in staging

## 9. Performance Testing (Planned)

Locust scenarios for event ingest and dashboard read load.

## 10. Security Testing (Planned)

- Bandit static analysis
- Auth bypass attempts
- Tenant isolation fuzz tests
- Pen test before production

## 11. UAT

Entry criteria: staging deploy green, P0 test cases pass, known defects triaged.

Exit criteria: stakeholder sign-off on intrusion/alert workflows.

## 12. Defect Severity

| Level | Definition |
|-------|------------|
| S1 | Production down or security breach |
| S2 | Major feature broken, no workaround |
| S3 | Minor feature issue with workaround |
| S4 | Cosmetic/documentation |
"""


def vol10_pm() -> str:
    return HEADER.format(vol="10", title="Project Management") + """
## 1. Program Overview

Deliver SentinelVision AI from MVP foundation to enterprise-ready hybrid security platform in phased releases.

## 2. Team Structure

| Role | Responsibility |
|------|----------------|
| Product Manager | Priorities, acceptance, stakeholder communication |
| Tech Lead | Architecture, code review, technical risk |
| Backend Engineers | Django API, data model, integrations |
| Frontend Engineers | Dashboard, UX implementation |
| ML/CV Engineers | Edge inference modules |
| DevOps Engineer | CI/CD, infrastructure, observability |
| QA Engineer | Test planning and automation |
| Security/Compliance | Privacy, audits, hardening |

## 3. Epics

| Epic | Description | Phase |
|------|-------------|-------|
| E1 Foundation | Auth, tenancy, cameras, docs, CI | M0/M1 |
| E2 Event Pipeline | RTSP, YOLO, ingest hardening | M2 |
| E3 Biometrics | Face, attendance, visitors | M3 |
| E4 Threat Detection | Weapon/fire/smoke | M4 |
| E5 Enterprise Ops | Reports, notifications, HA, SSO | M5 |

## 4. Sprint Plan (Indicative)

| Sprint | Goals | Points |
|--------|-------|--------|
| S1 | Documentation suite + tenant hardening | 34 |
| S2 | RTSP adapter + real YOLO integration | 40 |
| S3 | Zone intrusion + alert UX | 36 |
| S4 | Face enrollment + attendance | 42 |
| S5 | Notifications + reports | 38 |
| S6 | Production K8s + observability | 45 |

Story point scale: Fibonacci, team velocity assumed 35-40 points/sprint.

## 5. Timeline

| Milestone | Target | Exit Criteria |
|-----------|--------|---------------|
| M0/M1 Complete | Done | Foundation deployed locally |
| M2 Core AI | Week 10 | RTSP + person detection + intrusion |
| M3 Biometrics | Week 14 | Attendance + visitor check-in |
| M4 Threat | Week 18 | Weapon/fire/smoke modules |
| M5 Enterprise | Week 24 | HA, SSO, reporting, DR tested |

## 6. Budget Assumptions

| Category | Estimate (USD) | Notes |
|----------|----------------|-------|
| Engineering (6 FTE x 6 mo) | $450k-$600k | Region dependent |
| GPU edge hardware pilot | $15k-$40k | 3-5 sites |
| Cloud infrastructure | $3k-$8k/mo | Staging + prod |
| Third-party services | $1k-$3k/mo | SMS, email, monitoring |
| Security audit | $25k-$50k | Pre-production |

## 7. Risks

| ID | Risk | Impact | Mitigation |
|----|------|--------|------------|
| RISK-01 | False positive alert fatigue | High | Threshold tuning, human review |
| RISK-02 | Privacy non-compliance | High | Consent workflows, legal review |
| RISK-03 | Edge hardware variability | Medium | Certified hardware list |
| RISK-04 | Stream instability | High | Reconnect + health alerts |
| RISK-05 | Model bias | Medium | Fairness evaluation |
| RISK-06 | Tenant isolation defect | Critical | Expand isolation tests, remediate known gaps |

## 8. Release Plan

| Release | Scope |
|---------|-------|
| v0.1.0 | MVP foundation (current) |
| v0.2.0 | RTSP + YOLO + intrusion |
| v0.3.0 | Face + attendance + visitors |
| v0.4.0 | Threat modules + reports |
| v1.0.0 | Enterprise HA, SSO, production SLOs |

## 9. Governance

- Weekly sprint review and demo
- Bi-weekly architecture review
- Change control board for schema and API breaking changes
- Documentation updated per release tag

## 10. Final Deliverable Acceptance

- All P0 requirements Implemented or formally deferred
- Documentation suite regenerated and manifest published
- CI green on main branch
- Stakeholder UAT sign-off
- Production runbooks and DR test evidence
"""


def generate_traceability() -> None:
    rows = [
        "requirement_type,requirement_id,requirement_title,use_case,api_id,db_entity,test_id,status",
        "BR,BR-01,Reduce incident response time,UC-ALERT-01,API-ALERT-ACK,DB-Alert,TEST-E2E-001,Planned",
        "FR,FR-CAM-01,Register camera,UC-CAM-01,API-CAM-LIST,DB-Camera,TEST-API-003,Implemented",
        "FR,FR-DASH-01,Overview metrics,UC-AUTH-01,API-DASH-SUMMARY,DB-DetectionEvent,TEST-API-006,Implemented",
        "FR,FR-ALERT-04,Acknowledge alert,UC-ALERT-01,API-ALERT-ACK,DB-Alert,TEST-E2E-001,Planned",
        "NFR,NFR-01,Event ingest latency,UC-EVT-01,API-EVT-INGEST,DB-DetectionEvent,TEST-PERF-001,Planned",
        "AI,AI-FACE,Face recognition,UC-ATT-01,API-ATT-LIST,DB-PersonProfile,TEST-AI-001,Planned",
        "UI,UI-EVT,Event review,UC-EVT-02,API-EVT-REVIEW,DB-DetectionEvent,TEST-E2E-001,Partial",
        "OPS,OPS-CI,Continuous integration,,,,TEST-API-001,Implemented",
    ]
    path = ROOT / "docs" / "traceability-matrix.csv"
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"Generated {path}")


def write_unless_engineering_ready(name: str, content: str) -> None:
    """Do not overwrite volumes that have been hand-expanded to engineering-ready status."""
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if "status: engineering-ready" in existing[:500]:
            print(f"Preserved engineering-ready volume: {path}")
            return
    write(name, content)


def main() -> None:
    write("01-product-requirements.md", vol01_prd())
    write("02-software-requirements.md", vol02_srs())
    write_unless_engineering_ready("03-system-design.md", vol03_design())
    write_unless_engineering_ready("04-database-design.md", vol04_database())
    write_unless_engineering_ready("05-rest-api.md", vol05_api())
    write("06-ai-design.md", vol06_ai())
    write("07-ui-ux.md", vol07_ui())
    write("08-devops-deployment.md", vol08_devops())
    write("09-testing.md", vol09_testing())
    write("10-project-management.md", vol10_pm())
    generate_traceability()


if __name__ == "__main__":
    main()
