# SentinelVision AI — Enterprise Security Platform

Hybrid-deployment MVP foundation for an AI-powered smart security and activity monitoring platform.

## What's included

### Documentation Suite

Ten-volume enterprise documentation with reproducible PDF generation.

**Phase 1 engineering-ready (expanded):** Volumes 3, 4, and 5.

| Vol | Document | PDF |
|-----|----------|-----|
| 1 | [Product Requirements](docs/volumes/01-product-requirements.md) | [PDF](docs/pdf/01-product-requirements.pdf) |
| 2 | [Software Requirements](docs/volumes/02-software-requirements.md) | [PDF](docs/pdf/02-software-requirements.pdf) |
| 3 | [System Design](docs/volumes/03-system-design.md) **engineering-ready** | [PDF](docs/pdf/03-system-design.pdf) |
| 4 | [Database Design](docs/volumes/04-database-design.md) **engineering-ready** | [PDF](docs/pdf/04-database-design.pdf) |
| 5 | [REST API](docs/volumes/05-rest-api.md) **engineering-ready** | [PDF](docs/pdf/05-rest-api.pdf) |
| 6 | [AI Design](docs/volumes/06-ai-design.md) | [PDF](docs/pdf/06-ai-design.pdf) |
| 7 | [UI/UX](docs/volumes/07-ui-ux.md) | [PDF](docs/pdf/07-ui-ux.pdf) |
| 8 | [DevOps & Deployment](docs/volumes/08-devops-deployment.md) | [PDF](docs/pdf/08-devops-deployment.pdf) |
| 9 | [Testing](docs/volumes/09-testing.md) | [PDF](docs/pdf/09-testing.pdf) |
| 10 | [Project Management](docs/volumes/10-project-management.md) | [PDF](docs/pdf/10-project-management.pdf) |

**Combined suite:** [docs/pdf/enterprise-ai-smart-security-documentation-suite.pdf](docs/pdf/enterprise-ai-smart-security-documentation-suite.pdf)

**OpenAPI:** [docs/openapi-schema.yml](docs/openapi-schema.yml) · Swagger UI at `/api/docs/`

See [docs/README.md](docs/README.md) for build instructions, glossary, traceability matrix, and status legend.

Legacy single PRD: [docs/PRD.md](docs/PRD.md) | [docs/AI-Smart-Security-Platform-PRD.pdf](docs/AI-Smart-Security-Platform-PRD.pdf)

### Application stack

- **Backend** — Django + DRF multi-tenant API with JWT auth, cameras, events, alerts, audit
- **Frontend** — React + TypeScript dashboard (responsive / PWA-ready)
- **Edge** — Python edge service with simulated YOLO detection and event ingestion
- **Docker Compose** — Full local stack with PostgreSQL

## Quick start (Docker)

```bash
docker compose up --build
```

| Service   | URL                          |
|-----------|------------------------------|
| Dashboard | http://localhost:3000        |
| API       | http://localhost:8000/api/v1 |
| API Docs  | http://localhost:8000/api/docs/ |
| Health    | http://localhost:8000/api/v1/health/ |

**Demo login:** `admin` / `admin123`

## Local development (without Docker)

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # uses SQLite by default
python manage.py migrate
python manage.py seed_dev_data
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — API requests proxy to http://localhost:8000

### AI Vision (free, no API key)

Default mode uses on-device YOLOv4-tiny COCO-80. No signup and no API key.

1. Start backend + frontend
2. Open Cameras → live view → **AI Scan**
3. Open `/vision` to browse saved captures

Optional richer local LLM (still free, still no key): install [Ollama](https://ollama.com), run `ollama pull llava`, set `VISION_LLM_PROVIDER=ollama`.

### Edge service

```bash
cd edge
pip install -r requirements.txt
cp .env.example .env
python -m edge_service.main
```

## Generate documentation PDFs

```bash
pip install -r tools/requirements-docs.txt
python tools/generate_volumes.py
python tools/build_documentation.py
python tools/validate_documentation.py
```

Outputs: `docs/pdf/01-product-requirements.pdf` through `docs/pdf/10-project-management.pdf`, plus combined suite PDF and `docs/document-manifest.json`.

## API overview

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/token/` | JWT login |
| `GET /api/v1/dashboard/summary/` | Overview metrics |
| `GET /api/v1/cameras/` | Camera inventory |
| `GET /api/v1/events/` | Detection events |
| `POST /api/v1/events/ingest/` | Edge event ingestion |
| `POST /api/v1/cameras/{id}/vision/` | Capture frame + LLM scene analysis |
| `GET /api/v1/vision/captures/` | Saved AI Vision captures |
| `GET /api/v1/vision/status/` | Vision LLM configuration status |
| `GET /api/v1/alerts/` | Alert list |
| `POST /api/v1/edge/heartbeat/` | Edge heartbeat |
| `GET/POST /api/v1/persons/` | Person enrollment gallery |
| `POST /api/v1/face/match/` | Edge face recognition |
| `GET /api/v1/attendance/` | Attendance records |
| `GET/POST /api/v1/visitors/` | Visitor workflow |
| `GET /api/v1/unknown-sightings/` | Unknown person gallery |

Edge authentication uses the `X-Edge-API-Key` header.

## Testing

```bash
# Backend
cd backend && python -m pytest tests/ -q

# Edge
cd edge && python -m pytest tests/ -q

# Frontend
cd frontend && npm run lint && npm run build
```

## Architecture

```
Cameras → Edge AI (OpenCV/YOLO/InsightFace) → Django REST API → PostgreSQL
                                              ↓
                                         React Dashboard
```

## Milestones

**M2 detection pipeline** — [docs/M2-DETECTION-PIPELINE.md](docs/M2-DETECTION-PIPELINE.md)

**M3 face intelligence is implemented** — [docs/M3-FACE-INTELLIGENCE.md](docs/M3-FACE-INTELLIGENCE.md):

- Face detect / crop / blur / quality / align / best-face
- Person enrollment + biometric consent + embeddings
- InsightFace (or simulated) recognition → known / unknown
- Attendance clock-in/out with late & overtime
- Visitor request → approve → QR → check-in/out
- Unknown sighting gallery + alerts

**M4 advanced security analytics is implemented** — [docs/M4-ADVANCED-SECURITY-ANALYTICS.md](docs/M4-ADVANCED-SECURITY-ANALYTICS.md):

- Multi-zone intrusion with schedules, priority, entry/exit
- Loitering thresholds + escalation
- Crowd occupancy / density / heatmaps
- Object left / removed
- Risk correlation + configurable rule engine

**M5 life safety & emergency AI is implemented** — [docs/M5-LIFE-SAFETY-EMERGENCY-AI.md](docs/M5-LIFE-SAFETY-EMERGENCY-AI.md):

- Multi-frame fire verification + optional evidence clips
- Smoke density, trend, persistence, and escalation
- Weapon↔person-track association
- Fall confirmation, immobility, and recovery
- Zone/shift/role-aware PPE compliance
- Unified emergency incidents, actions, escalation, and command center

**M6 enterprise operations** — [docs/M6-ENTERPRISE-OPERATIONS.md](docs/M6-ENTERPRISE-OPERATIONS.md):

- Priority 1: composite edge dedupe, zone validation, unified ingest pipeline
- M6.1 Celery notification workers (retry, DLQ, rate limits, delivery logs, multi-channel)
- M6.2 Evidence storage (local/MinIO/S3) with signed URLs + rich metadata
- M6.3 Recording adapters (RTSP + vendor stubs: ONVIF/Hikvision/Dahua/Milestone/Axis)
- M6.4 SSO provider config, password/session policies, MFA flags
- M6.5 Prometheus metrics + ready/live probes
- M6.6–6.8 Compose Redis/Celery/MinIO, SIEM forwards, backup/restore scripts (RPO≤15m / RTO≤1h)

**GA remaining:** vendor NVR SDKs, full IdP handshake libs per deploy, load/security testing.

## License

Proprietary — Internal use only.
