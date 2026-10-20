# SentinelVision AI — Enterprise Documentation Suite

Professional documentation for the AI Smart Security & Activity Monitoring Platform.

## Volumes

| Vol | Document | Source | PDF |
|-----|----------|--------|-----|
| 1 | Product Requirements Document | [volumes/01-product-requirements.md](volumes/01-product-requirements.md) | [pdf/01-product-requirements.pdf](pdf/01-product-requirements.pdf) |
| 2 | Software Requirements Specification | [volumes/02-software-requirements.md](volumes/02-software-requirements.md) | [pdf/02-software-requirements.pdf](pdf/02-software-requirements.pdf) |
| 3 | System Design Document | [volumes/03-system-design.md](volumes/03-system-design.md) | [pdf/03-system-design.pdf](pdf/03-system-design.pdf) |
| 4 | Database Design | [volumes/04-database-design.md](volumes/04-database-design.md) | [pdf/04-database-design.pdf](pdf/04-database-design.pdf) |
| 5 | REST API Documentation | [volumes/05-rest-api.md](volumes/05-rest-api.md) | [pdf/05-rest-api.pdf](pdf/05-rest-api.pdf) |
| 6 | AI Design Document | [volumes/06-ai-design.md](volumes/06-ai-design.md) | [pdf/06-ai-design.pdf](pdf/06-ai-design.pdf) |
| 7 | UI/UX Specification | [volumes/07-ui-ux.md](volumes/07-ui-ux.md) | [pdf/07-ui-ux.pdf](pdf/07-ui-ux.pdf) |
| 8 | DevOps & Deployment | [volumes/08-devops-deployment.md](volumes/08-devops-deployment.md) | [pdf/08-devops-deployment.pdf](pdf/08-devops-deployment.pdf) |
| 9 | Testing Documentation | [volumes/09-testing.md](volumes/09-testing.md) | [pdf/09-testing.pdf](pdf/09-testing.pdf) |
| 10 | Project Management | [volumes/10-project-management.md](volumes/10-project-management.md) | [pdf/10-project-management.pdf](pdf/10-project-management.pdf) |

**Combined suite PDF:** [pdf/enterprise-ai-smart-security-documentation-suite.pdf](pdf/enterprise-ai-smart-security-documentation-suite.pdf)

## Supporting artifacts

- [shared/glossary.md](shared/glossary.md)
- [shared/status-legend.md](shared/status-legend.md)
- [traceability-matrix.csv](traceability-matrix.csv)
- [document-manifest.json](document-manifest.json)
- [diagrams/](diagrams/)

## Build commands

```bash
pip install -r tools/requirements-docs.txt
python tools/build_documentation.py
python tools/validate_documentation.py
```

Legacy single PRD build remains available:

```bash
python tools/build_prd.py
```

## Engineering-ready volumes (Phase 1)

Volumes **3 (System Design)**, **4 (Database Design)**, and **5 (REST API)** are expanded to engineering-ready depth:

- Complete endpoint contracts with request/response examples
- PostgreSQL DDL, indexes, constraints, and planned triggers
- Django app architecture, RTSP pipeline, Celery/Redis, and deployment diagrams

These files are marked `status: engineering-ready` and are **not overwritten** by `tools/generate_volumes.py`.

## Phase 2 development map

| Milestone | Focus | Code status |
|-----------|-------|-------------|
| M1 | Django, JWT, RBAC, multi-tenant orgs/sites/cameras, dashboard | **Implemented** (MVP foundation) |
| M2 | RTSP, OpenCV, YOLO, detection pipeline, event storage | Next |
| M3 | InsightFace, enrollment, recognition, attendance | Planned |
| M4 | Intrusion, unknown person, visitors | Planned |
| M5 | Fire, smoke, weapon detection | Future |
| M6 | Reports, notifications, mobile, analytics | Future |
