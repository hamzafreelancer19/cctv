# M3 — Face Intelligence

**Status:** Implemented (Sprints 1–6)

Face detection, enrollment, recognition, attendance, visitors, and unknown-person gallery.

| Sprint | Scope | Status |
|--------|-------|--------|
| 1 | Face detect, crop, blur, quality, align, best face | Done |
| 2 | Enrollment API + persons / embeddings / images | Done |
| 3 | InsightFace match → known / unknown | Done |
| 4 | Attendance clock in/out, late, overtime, reports | Done |
| 5 | Visitor request → approve → QR → check-in/out | Done |
| 6 | Unknown gallery + alerts | Done |

Notes: host email/SMS for visitors is stubbed (`metadata.host_notified`). InsightFace is optional (`FACE_BACKEND=auto` falls back to simulated embeddings).

## Pipeline

```
Person Track
    │
Face Detector (OpenCV Haar + quality/blur)
    │
Face Align 112x112
    │
Embedder (InsightFace or simulated)
    │
POST /api/v1/face/match/
    │
Known → attendance / visitor check-in / blacklist alert
Unknown → UnknownSighting + alert
```

## Backend (`apps.identity`)

| Model | Purpose |
|-------|---------|
| Person | Employee / visitor / VIP / blacklist / unknown |
| BiometricConsent | Required before enrollment |
| FaceImage | Uploaded / captured faces |
| FaceEmbedding | Vector gallery |
| AttendanceRecord | Clock in/out, late, overtime |
| VisitorRegistration | Request → approve → QR → check-in/out |
| UnknownSighting | Unrecognized faces gallery |

### Key APIs

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `GET/POST /api/v1/persons/` | JWT | Person CRUD |
| `POST /api/v1/persons/enroll/` | JWT Admin | Consent-gated enrollment |
| `POST /api/v1/consents/` | JWT Admin | Biometric consent |
| `GET /api/v1/face/gallery/` | Edge key | Embedding export |
| `POST /api/v1/face/match/` | Edge key | Recognize + attendance/unknown |
| `GET /api/v1/attendance/` | JWT | Attendance list |
| `GET /api/v1/attendance/report/` | JWT | Daily/weekly aggregates |
| `GET/POST /api/v1/visitors/` | JWT | Visitor workflow |
| `POST /api/v1/visitors/{id}/{action}/` | JWT | approve/deny/checkin/checkout |
| `GET /api/v1/unknown-sightings/` | JWT | Unknown gallery |

## Edge modules

| Module | Path |
|--------|------|
| Face detector | `edge/edge_service/face/detector.py` |
| Embedder | `edge/edge_service/face/embedder.py` |
| Pipeline hook | `edge/edge_service/pipeline.py` |

Env flags: `ENABLE_FACE=true`, `FACE_BACKEND=auto|insightface|simulated`, `FACE_MATCH_THRESHOLD=0.45`

## Dashboard

People, Attendance, Visitors, Unknown pages under the sidebar.

## Roadmap after M3

- **M4:** Implemented — see [M4-ADVANCED-SECURITY-ANALYTICS.md](M4-ADVANCED-SECURITY-ANALYTICS.md)
- **M5:** fire/smoke/weapon/fall/PPE detectors
- **M6:** notifications (email/WhatsApp/SMS), mobile, analytics, SSO, DR
