---
volume: 01
title: Product Requirements Document
status: draft
---

# Product Requirements Document

> **SentinelVision AI — Enterprise Documentation Suite**
> Status legend: Implemented | Planned | Future


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
