---
volume: 09
title: Testing Documentation
status: draft
---

# Testing Documentation

> **SentinelVision AI — Enterprise Documentation Suite**
> Status legend: Implemented | Planned | Future


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
| TEST-API-001 | Health endpoint returns healthy | Implemented | FR-DASH-01 |
| TEST-API-002 | JWT login returns tokens | Implemented | UC-AUTH-01 |
| TEST-API-003 | Tenant camera isolation | Implemented | BR-TEN-01 |
| TEST-API-004 | Event ingest creates event | Implemented | UC-EVT-01 |
| TEST-API-005 | Duplicate edge_event_id idempotent | Implemented | UC-EVT-01 |
| TEST-API-006 | Dashboard summary metrics | Implemented | FR-DASH-01 |
| TEST-EDGE-001 | Simulated detector structure | Implemented | AI-TRACK |
| TEST-EDGE-002 | Event payload builder | Implemented | API-EVT-INGEST |
| TEST-UI-001 | API base defaults to /api/v1 | Implemented | UI-DASH |
| TEST-API-007 | RBAC denies viewer config write | Planned | FR-CAM-01 |
| TEST-API-008 | Cross-tenant ingest forbidden | Planned | BR-EDGE-01 |
| TEST-E2E-001 | Login to alert acknowledgement | Planned | UC-ALERT-01 |
| TEST-AI-001 | YOLO precision on validation set | Planned | AI-FACE |
| TEST-PERF-001 | Ingest 100 events/sec soak | Planned | NFR-01 |
| TEST-SEC-001 | OWASP API top 10 scan | Planned | NFR-05 |

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
