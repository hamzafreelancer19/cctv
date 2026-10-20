# Product Requirements Document
## AI Smart Security & Activity Monitoring Platform

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 |
| **Status** | Approved for MVP Development |
| **Date** | July 17, 2026 |
| **Product Name** | SentinelVision AI |
| **Classification** | Internal / Confidential |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Business Goals & KPIs](#2-business-goals--kpis)
3. [Product Vision & Scope](#3-product-vision--scope)
4. [Assumptions & Constraints](#4-assumptions--constraints)
5. [User Personas](#5-user-personas)
6. [User Stories](#6-user-stories)
7. [Functional Requirements](#7-functional-requirements)
8. [AI Modules](#8-ai-modules)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [System Architecture](#10-system-architecture)
11. [Database Overview](#11-database-overview)
12. [REST API Strategy](#12-rest-api-strategy)
13. [Security & Privacy Controls](#13-security--privacy-controls)
14. [Hardware Requirements](#14-hardware-requirements)
15. [Technology Stack](#15-technology-stack)
16. [Deployment Architecture](#16-deployment-architecture)
17. [Development Roadmap & Milestones](#17-development-roadmap--milestones)
18. [Testing Strategy](#18-testing-strategy)
19. [Risks & Mitigations](#19-risks--mitigations)
20. [MVP Definition & Future Roadmap](#20-mvp-definition--future-roadmap)

---

## 1. Executive Summary

SentinelVision AI is an enterprise-grade, multi-tenant platform that transforms existing CCTV infrastructure into an intelligent security and activity monitoring system. The platform combines computer vision, deep learning, and real-time alerting to detect threats, track people, manage visitors, automate attendance, and provide actionable operational insights.

**Deployment model:** Hybrid — AI inference and video processing occur on-premise at the customer edge; metadata, dashboards, notifications, and reporting are managed through a centralized control plane.

**Primary value proposition:**
- Reduce security incident response time by 60%+
- Automate attendance and visitor workflows
- Detect intrusions, weapons, fire/smoke, and unknown persons in real time
- Provide audit-ready evidence trails without storing raw video in the cloud by default

**Target customers:** Corporate campuses, manufacturing facilities, warehouses, educational institutions, healthcare facilities, and government buildings with 16–500+ cameras.

---

## 2. Business Goals & KPIs

| Goal | Description | KPI | Target (12 months) |
|------|-------------|-----|-------------------|
| G1 | Reduce security response time | Mean time to acknowledge critical alert | < 2 minutes |
| G2 | Improve threat detection | True positive rate for intrusion/weapon | ≥ 92% |
| G3 | Automate attendance | Manual attendance reconciliation hours/week | -80% |
| G4 | Visitor compliance | Pre-registered visitor check-in accuracy | ≥ 98% |
| G5 | Platform reliability | Control plane uptime | 99.9% |
| G6 | Customer adoption | Active sites per tenant | ≥ 3 |
| G7 | Privacy compliance | Biometric consent coverage | 100% enrolled staff |

---

## 3. Product Vision & Scope

### 3.1 Vision Statement

*"Every camera becomes an intelligent sensor — protecting people, assets, and operations with privacy-respecting AI that security teams can trust."*

### 3.2 In Scope (Phase 1–3)

- Multi-tenant organization, site, and zone management
- Camera registry with RTSP/ONVIF connectivity
- Edge AI inference pipeline (person, face, activity, threat detection)
- Real-time event ingestion, alert rules, and notification delivery
- Web dashboard with event review queue and operational reports
- Mobile-responsive PWA for alerts and approvals
- RBAC, audit logging, and biometric consent management
- REST API v1 with OpenAPI documentation

### 3.3 Out of Scope (MVP)

- Native iOS/Android apps (Phase 4)
- Full VMS replacement (integrates with existing NVR/VMS)
- Automated law enforcement integration
- Cloud-stored continuous video archive
- Custom model training UI (Phase 3+)

---

## 4. Assumptions & Constraints

| ID | Assumption / Constraint |
|----|------------------------|
| A1 | Customers have IP cameras supporting RTSP or ONVIF |
| A2 | Edge hardware includes NVIDIA GPU (Jetson or discrete) |
| A3 | Network bandwidth between edge and control plane ≥ 10 Mbps |
| A4 | Biometric processing requires explicit employee consent |
| A5 | Raw video remains on-premise; only metadata and clips upload on alert |
| A6 | Platform supports English UI in MVP; i18n in Phase 3 |
| C1 | GDPR/local privacy laws govern retention and consent |
| C2 | False positives require human-in-the-loop review workflow |

---

## 5. User Personas

| Persona | Role | Goals | Pain Points |
|---------|------|-------|-------------|
| **Sarah — Security Manager** | SOC lead | Monitor all sites, respond to threats, audit incidents | Alert fatigue, fragmented tools |
| **Ahmed — Facility Admin** | IT/ops | Configure cameras, manage users, ensure uptime | Complex integrations, no single pane |
| **Priya — HR Manager** | HR | Attendance, visitor compliance | Manual logs, no real-time visibility |
| **James — Edge Technician** | Field engineer | Install edge nodes, troubleshoot cameras | Opaque AI pipeline, hard diagnostics |
| **Maria — Executive** | C-suite | Risk dashboards, compliance reports | No aggregated KPI view |

---

## 6. User Stories

### 6.1 Security Operations

| ID | Story | Priority |
|----|-------|----------|
| US-01 | As a Security Manager, I want real-time intrusion alerts so I can dispatch guards within 2 minutes | P0 |
| US-02 | As a Security Manager, I want to review detection events with snapshot evidence so I can confirm true positives | P0 |
| US-03 | As a Security Manager, I want unknown person alerts in restricted zones so unauthorized access is flagged | P0 |
| US-04 | As a Security Manager, I want weapon/fire/smoke alerts with severity levels so I can escalate appropriately | P0 |

### 6.2 Administration

| ID | Story | Priority |
|----|-------|----------|
| US-05 | As a Facility Admin, I want to register cameras and assign them to sites/zones | P0 |
| US-06 | As a Facility Admin, I want RBAC so operators cannot change system configuration | P0 |
| US-07 | As a Facility Admin, I want edge device health monitoring so I know when inference is offline | P1 |

### 6.3 HR & Visitor Management

| ID | Story | Priority |
|----|-------|----------|
| US-08 | As HR, I want automated attendance from face recognition at entry points | P1 |
| US-09 | As HR, I want visitor pre-registration and check-in/out logs | P1 |
| US-10 | As HR, I want consent records before enrolling biometric profiles | P0 |

### 6.4 Reporting & Compliance

| ID | Story | Priority |
|----|-------|----------|
| US-11 | As an Executive, I want weekly incident summary reports | P1 |
| US-12 | As a Compliance Officer, I want immutable audit logs for all configuration changes | P0 |

---

## 7. Functional Requirements

### 7.1 Camera Management

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-CAM-01 | Register cameras with name, RTSP URL, site, zone, status | P0 |
| FR-CAM-02 | Support ONVIF discovery (Phase 2) | P2 |
| FR-CAM-03 | Monitor camera online/offline heartbeat from edge | P0 |
| FR-CAM-04 | Assign AI modules per camera (face, intrusion, weapon, etc.) | P1 |
| FR-CAM-05 | Configure detection zones (polygons) per camera | P1 |

### 7.2 Dashboard

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-DASH-01 | Overview: active cameras, events today, open alerts, edge status | P0 |
| FR-DASH-02 | Event review queue with filters (type, severity, site, date) | P0 |
| FR-DASH-03 | Live camera status grid | P1 |
| FR-DASH-04 | Role-based navigation and data scoping | P0 |

### 7.3 Alerts & Notifications

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-ALERT-01 | Configurable alert rules (event type, zone, threshold, schedule) | P0 |
| FR-ALERT-02 | Severity levels: Info, Warning, Critical | P0 |
| FR-ALERT-03 | Notification channels: in-app, email (SMS Phase 2) | P0 |
| FR-ALERT-04 | Alert acknowledgement and resolution workflow | P0 |

### 7.4 Reports

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-RPT-01 | Daily/weekly incident summary export (PDF/CSV) | P1 |
| FR-RPT-02 | Attendance report by employee and date range | P1 |
| FR-RPT-03 | Visitor log report | P1 |
| FR-RPT-04 | Audit log export | P0 |

### 7.5 Mobile Experience

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-MOB-01 | Responsive web UI for alert list and acknowledgement | P0 |
| FR-MOB-02 | PWA install support with push notifications (Phase 2) | P2 |
| FR-MOB-03 | Native mobile apps (Phase 4) | P3 |

---

## 8. AI Modules

| Module | Description | Input | Output | Model/Tech | MVP |
|--------|-------------|-------|--------|------------|-----|
| **Face Recognition** | Identify enrolled employees/visitors | Video frame, face bbox | Person ID, confidence, embedding | InsightFace | Phase 2 |
| **Multi-Person Tracking** | Track individuals across frames/cameras | Video stream | Track IDs, trajectories | YOLO + DeepSORT/ByteTrack | Phase 2 |
| **Activity Recognition** | Detect loitering, running, fighting, fall | Track + pose | Activity class, confidence | YOLO-Pose / custom | Phase 3 |
| **Intrusion Detection** | Person in restricted zone after hours | Zone polygon + detections | Intrusion event | YOLO + zone logic | Phase 2 |
| **Unknown Person Detection** | Face not in enrolled gallery | Face embedding | Unknown person alert | InsightFace + threshold | Phase 2 |
| **Visitor Management** | Match pre-registered visitors | Face + visitor DB | Check-in event | InsightFace + API | Phase 2 |
| **Attendance** | Clock-in/out at entry cameras | Face recognition | Attendance record | InsightFace + rules | Phase 2 |
| **Fire/Smoke Detection** | Visual fire/smoke cues | Video frame | Fire/smoke alert | YOLO custom / pretrained | Phase 3 |
| **Weapon Detection** | Detect firearms/knives | Video frame | Weapon alert | YOLO custom | Phase 3 |

### 8.1 AI Pipeline Flow

```
Camera Stream → Frame Sampling → Person Detection (YOLO)
  → Tracking → Face Detection → Embedding (InsightFace)
  → Module Router → Event Builder → Edge Buffer → Control Plane API
```

### 8.2 Model Governance

- Model version tracked per detection event
- Confidence threshold configurable per module
- Human review required for biometric identification below threshold
- Model updates deployed via edge OTA package (Phase 3)

---

## 9. Non-Functional Requirements

| Category | Requirement | Target |
|----------|-------------|--------|
| **Performance** | Event ingestion latency (edge → API) | < 3 seconds p95 |
| **Performance** | Dashboard page load | < 2 seconds |
| **Performance** | Edge inference FPS per camera (1080p) | ≥ 15 FPS (1 module) |
| **Scalability** | Cameras per edge node | Up to 16 (GPU dependent) |
| **Scalability** | Tenants on shared control plane | 100+ |
| **Availability** | Control plane uptime | 99.9% |
| **Security** | Data in transit | TLS 1.2+ |
| **Security** | Data at rest | AES-256 |
| **Privacy** | Biometric consent before enrollment | Mandatory |
| **Retention** | Event metadata default retention | 90 days (configurable) |
| **Retention** | Evidence clips default retention | 30 days |
| **Accessibility** | WCAG 2.1 Level AA (Phase 2) | Target |
| **Localization** | UTC timestamps, tenant timezone display | MVP |

---

## 10. System Architecture

### 10.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CUSTOMER PREMISES (EDGE)                     │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────────────┐   │
│  │ IP       │───▶│ Edge AI      │───▶│ Encrypted Event     │   │
│  │ Cameras  │    │ Service      │    │ Buffer (local)      │   │
│  └──────────┘    │ OpenCV+YOLO  │    └──────────┬──────────┘   │
│                  │ +InsightFace │               │               │
│                  └──────────────┘               │ TLS           │
└─────────────────────────────────────────────────┼───────────────┘
                                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CONTROL PLANE (CLOUD / DC)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Django REST  │  │ PostgreSQL   │  │ Object Storage       │  │
│  │ API          │──│ Database     │  │ (evidence clips)     │  │
│  └──────┬───────┘  └──────────────┘  └──────────────────────┘  │
│         │                                                        │
│  ┌──────▼───────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ React Web    │  │ Background   │  │ Notification         │  │
│  │ Dashboard    │  │ Jobs (Celery)│  │ Email / SMS / Push   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| Edge AI Service | Stream ingestion, inference, event packaging, offline buffer |
| Django REST API | Auth, tenancy, CRUD, event ingestion, alert engine |
| PostgreSQL | Relational data, audit logs, event index |
| React Dashboard | Operations UI, review workflows, configuration |
| Background Jobs | Report generation, notification dispatch, retention cleanup |
| Object Storage | Alert snapshot and clip storage (S3-compatible) |

### 10.3 Event Flow

1. Edge samples frames from RTSP stream
2. YOLO detects persons/objects; tracker assigns IDs
3. Module router evaluates zone rules and runs specialized models
4. Event builder creates structured payload with metadata
5. Edge POSTs to `/api/v1/events/ingest/` with API key
6. API validates, persists, evaluates alert rules
7. Critical alerts trigger notifications and appear in dashboard queue

---

## 11. Database Overview

### 11.1 Core Entities

| Entity | Key Fields | Relationships |
|--------|-----------|---------------|
| Organization | id, name, slug, settings | Has many Sites, Users |
| Site | id, org_id, name, address, timezone | Has many Cameras, Zones |
| UserMembership | user_id, org_id, role | Links User to Organization |
| Camera | id, site_id, name, rtsp_url, status, modules | Belongs to Site, Zone |
| Zone | id, site_id, name, polygon_json | Belongs to Site |
| EdgeDevice | id, site_id, name, api_key_hash, last_seen | Belongs to Site |
| DetectionEvent | id, camera_id, type, confidence, payload, review_status | Belongs to Camera |
| AlertRule | id, org_id, event_type, severity, conditions | Belongs to Organization |
| Alert | id, event_id, rule_id, status, acknowledged_by | Belongs to Event |
| AuditLog | id, org_id, actor_id, action, resource, timestamp | Immutable |

### 11.2 Indexing Strategy

- `DetectionEvent`: index on (organization_id, created_at DESC), (camera_id, type)
- `Alert`: index on (organization_id, status, created_at)
- `AuditLog`: index on (organization_id, timestamp)

---

## 12. REST API Strategy

### 12.1 Principles

- Versioned base path: `/api/v1/`
- JSON request/response; ISO 8601 timestamps (UTC)
- UUID primary keys in API responses
- Cursor-based pagination for events (`?cursor=`)
- OpenAPI 3 schema at `/api/schema/`
- JWT Bearer auth for users; API key for edge devices

### 12.2 Core Endpoints (v1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/token/` | Obtain JWT access/refresh tokens |
| GET | `/api/v1/organizations/` | List user's organizations |
| GET/POST | `/api/v1/sites/` | Site CRUD |
| GET/POST | `/api/v1/cameras/` | Camera CRUD |
| GET/POST | `/api/v1/zones/` | Zone CRUD |
| GET | `/api/v1/events/` | List detection events (filtered) |
| POST | `/api/v1/events/ingest/` | Edge event ingestion |
| GET/PATCH | `/api/v1/events/{id}/review/` | Human review workflow |
| GET/POST | `/api/v1/alerts/` | Alert list and rules |
| PATCH | `/api/v1/alerts/{id}/acknowledge/` | Acknowledge alert |
| GET | `/api/v1/dashboard/summary/` | Overview metrics |
| GET | `/api/v1/audit-logs/` | Audit trail |
| POST | `/api/v1/edge/heartbeat/` | Edge device heartbeat |

### 12.3 Error Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": {}
  }
}
```

---

## 13. Security & Privacy Controls

| Control | Implementation |
|---------|----------------|
| Authentication | JWT (access 15 min, refresh 7 days) |
| Authorization | RBAC: Owner, Admin, Operator, Viewer |
| Tenant isolation | All queries scoped by organization_id |
| Edge authentication | Per-device API key, rotated quarterly |
| Encryption in transit | TLS 1.2+ everywhere |
| Encryption at rest | PostgreSQL TDE / disk encryption; S3 SSE |
| Biometric consent | Consent record required before face enrollment |
| Data minimization | No raw video upload by default |
| Audit logging | All config changes and auth events logged |
| Rate limiting | 100 req/min per user; 1000 req/min per edge device |
| Secret management | Environment variables / vault; never in source |
| Vulnerability management | Dependabot, quarterly penetration test |

---

## 14. Hardware Requirements

### 14.1 Edge Node (per site)

| Spec | Minimum | Recommended |
|------|---------|-------------|
| CPU | 8-core x86 | 12-core x86 |
| RAM | 16 GB | 32 GB |
| GPU | NVIDIA GTX 1660 / Jetson Orin Nano | RTX 3060 / Jetson AGX Orin |
| Storage | 256 GB SSD | 512 GB NVMe |
| Network | 1 Gbps LAN | 1 Gbps LAN |
| Cameras supported | 4–8 | 12–16 |

### 14.2 Control Plane (per deployment)

| Spec | Minimum | Recommended |
|------|---------|-------------|
| CPU | 4 vCPU | 8 vCPU |
| RAM | 8 GB | 16 GB |
| Database | PostgreSQL 15+, 100 GB SSD | HA cluster, 500 GB |
| Object storage | 1 TB S3-compatible | Scalable bucket |

---

## 15. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Python 3.12+, Django 5.x | Web framework |
| API | Django REST Framework | REST API |
| Auth | djangorestframework-simplejwt | JWT authentication |
| Database | PostgreSQL 15+ | Primary datastore |
| Task queue | Celery + Redis (Phase 2) | Async jobs |
| Frontend | React 18+, TypeScript, Vite | Dashboard SPA |
| UI | Custom CSS / lightweight components | Responsive UI |
| CV / Detection | OpenCV, Ultralytics YOLO | Stream processing, detection |
| Face | InsightFace | Face detection & recognition |
| Tracking | ByteTrack / DeepSORT | Multi-person tracking |
| Edge runtime | Python service + GStreamer/FFmpeg | RTSP ingestion |
| Containerization | Docker, Docker Compose | Dev & deployment |
| CI | GitHub Actions | Automated testing |
| Docs | OpenAPI (drf-spectacular) | API documentation |

---

## 16. Deployment Architecture

### 16.1 Environments

| Environment | Purpose | Data |
|-------------|---------|------|
| Development | Local Docker Compose | Synthetic |
| Staging | Pre-production validation | Anonymized |
| Production | Customer-facing | Live |

### 16.2 Hybrid Deployment Topology

- **Edge:** Docker container on customer hardware; outbound-only HTTPS to control plane
- **Control plane:** Kubernetes or Docker Swarm behind load balancer
- **Database:** Managed PostgreSQL with automated backups
- **Storage:** S3-compatible bucket for evidence artifacts

### 16.3 Network Requirements

- Edge → API: HTTPS 443 outbound
- Cameras → Edge: RTSP 554 internal LAN
- Admin → Dashboard: HTTPS 443

---

## 17. Development Roadmap & Milestones

| Phase | Timeline | Deliverables |
|-------|----------|-------------|
| **M0 — Foundation** | Weeks 1–3 | PRD, repo scaffold, auth, tenancy, camera registry, Docker, CI |
| **M1 — Event Pipeline** | Weeks 4–6 | Edge service, simulated detection, event ingest, dashboard queue |
| **M2 — Core AI** | Weeks 7–10 | YOLO person detection, tracking, intrusion zones, alerts |
| **M3 — Biometrics** | Weeks 11–14 | Face enrollment, recognition, attendance, unknown person |
| **M4 — Threat Modules** | Weeks 15–18 | Weapon, fire/smoke detection, escalation workflows |
| **M5 — Enterprise** | Weeks 19–24 | Reports, visitor management, HA, SSO, audit export |

### 17.1 Milestone Acceptance Criteria (M0)

- [ ] Multi-tenant Django API with JWT auth
- [ ] Camera and site CRUD with RBAC
- [ ] React dashboard with login and overview
- [ ] Edge heartbeat and event ingest endpoints
- [ ] Docker Compose local stack running
- [ ] CI pipeline passing unit and API tests
- [ ] PRD PDF generated from source

---

## 18. Testing Strategy

| Level | Scope | Tools |
|-------|-------|-------|
| Unit | Models, serializers, permissions, edge client | pytest, Django TestCase |
| Integration | API endpoints, tenant isolation | pytest + DRF APIClient |
| E2E | Login → view events → acknowledge alert | Playwright (Phase 2) |
| Performance | Event ingest throughput | Locust |
| Security | OWASP top 10, auth bypass | Bandit, manual review |
| AI accuracy | Module precision/recall on test set | Custom benchmark suite |

**Coverage target:** ≥ 80% for backend core apps.

---

## 19. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| High false positive rate | Alert fatigue, ignored alerts | High | Confidence tuning, human review, feedback loop |
| Privacy regulation breach | Legal liability | Medium | Consent workflow, data minimization, DPO review |
| Edge hardware variability | Performance inconsistency | Medium | Certified hardware list, benchmark on install |
| Camera stream instability | Missed detections | High | Reconnect logic, health alerts, redundant paths |
| Model bias | Discriminatory outcomes | Medium | Diverse training data, fairness audits |
| Network outage at edge | Event loss | Medium | Local encrypted buffer, replay on reconnect |

---

## 20. MVP Definition & Future Roadmap

### 20.1 MVP (M0 + M1)

**Included:**
- Organization/site/camera management
- JWT auth and RBAC
- Edge registration and heartbeat
- Simulated person detection events
- Event list and alert acknowledgement in dashboard
- Audit logging for configuration changes
- Docker-based local deployment

**Excluded from MVP:**
- Production-grade YOLO/InsightFace accuracy
- Face enrollment and attendance
- Weapon/fire/smoke modules
- SMS notifications
- Native mobile apps
- SSO/SAML

### 20.2 Future Roadmap

| Quarter | Features |
|---------|----------|
| Q3 2026 | Production AI modules, zone-based intrusion, email alerts |
| Q4 2026 | Face recognition, attendance, visitor management, reports |
| Q1 2027 | Weapon/fire/smoke, activity recognition, PWA push |
| Q2 2027 | Multi-site analytics, SSO, model OTA, native mobile |
| Q3 2027 | Custom model training portal, third-party VMS integrations |

---

## Appendix A — Glossary

| Term | Definition |
|------|-----------|
| Edge | On-premise compute node running AI inference |
| Control Plane | Centralized API and dashboard services |
| Detection Event | Structured record of an AI inference result |
| Zone | Polygon region on a camera view for rule evaluation |

---

## Appendix B — Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-17 | Product Engineering | Initial PRD for MVP development |

---

*End of Document*
