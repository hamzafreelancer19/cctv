---
volume: 10
title: Project Management
status: draft
---

# Project Management

> **SentinelVision AI — Enterprise Documentation Suite**
> Status legend: Implemented | Planned | Future


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
