---
volume: 05
title: REST API Documentation
status: engineering-ready
version: 2.0.0
---

# REST API Documentation

> **SentinelVision AI — Volume 5**
> Status: Implemented | Planned | Future

## 1. Document Control

| Field | Value |
|-------|-------|
| Document ID | DOC-API-005 |
| Version | 2.0.0 |
| Status | Engineering Ready |
| Base URL (local) | `http://localhost:8000` |
| API Prefix | `/api/v1/` |
| OpenAPI Schema | `GET /api/schema/` |
| Swagger UI | `GET /api/docs/` |

## 2. API Conventions

| Convention | Specification |
|------------|---------------|
| Protocol | HTTP/1.1 (TLS 1.2+ in production) |
| Content-Type | `application/json` |
| Charset | UTF-8 |
| Timestamps | ISO 8601 UTC (`2026-07-17T07:00:00.000000Z`) |
| Primary keys | UUID v4 in path and response |
| Pagination | PageNumberPagination, `PAGE_SIZE=25` (Implemented); cursor Planned |
| Filtering | `django-filter` query params where documented |
| Ordering | `?ordering=field` or `?ordering=-field` |
| Search | `?search=term` where documented |

### 2.1 Authentication Methods

| Method | Header | Used By | Status |
|--------|--------|---------|--------|
| JWT Bearer | `Authorization: Bearer <access_token>` | Dashboard users | Implemented |
| Edge API Key | `X-Edge-API-Key: <raw_key>` | Edge workers | Implemented |
| Edge Alt | `Authorization: Edge <raw_key>` | Edge workers | Implemented |

### 2.2 JWT Token Policy

| Token | Lifetime | Notes |
|-------|----------|-------|
| Access | 15 minutes | Used for API calls |
| Refresh | 7 days | `ROTATE_REFRESH_TOKENS=True`; blacklist Planned |

### 2.3 Role Permissions Matrix

| Capability | Owner | Admin | Operator | Viewer |
|------------|-------|-------|----------|--------|
| Read org/sites/cameras/events/alerts | Yes | Yes | Yes | Yes |
| Create/update/delete sites, zones, cameras | Yes | Yes | No | No |
| Create edge devices | Yes | Yes | No | No |
| Create alert rules | Yes | Yes | No | No |
| Review events | Yes | Yes | Yes | No |
| Acknowledge/resolve alerts | Yes | Yes | Yes | No |
| List audit logs | Yes | Yes | Yes | Yes |

### 2.4 Standard Error Responses

**Current (DRF default) for most endpoints:**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

```json
{
  "field_name": ["This field is required."]
}
```

**Target envelope (Planned — use for new endpoints):**

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable summary",
    "details": {"field": ["reason"]}
  }
}
```

| HTTP | Code (Planned) | Meaning |
|------|----------------|---------|
| 400 | VALIDATION_ERROR | Invalid request body/query |
| 401 | UNAUTHENTICATED | Missing or invalid credentials |
| 403 | FORBIDDEN | Authenticated but insufficient role/tenant |
| 404 | NOT_FOUND | Resource does not exist or not visible |
| 409 | CONFLICT | Duplicate / state conflict |
| 429 | RATE_LIMITED | Too many requests (Planned) |
| 500 | INTERNAL_ERROR | Unexpected server error |

### 2.5 Pagination Envelope

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/events/?page=2",
  "previous": null,
  "results": []
}
```

---

## 3. Health & Schema

### API-HEALTH — Health Check

| Field | Value |
|-------|-------|
| Method / URL | `GET /api/v1/health/` |
| Auth | None |
| Permissions | Public |
| Status | Implemented |

**Response `200`:**

```json
{
  "status": "healthy",
  "service": "sentinelvision-api",
  "timestamp": "2026-07-17T07:00:00.123456+00:00"
}
```

### API-SCHEMA — OpenAPI Schema

| Field | Value |
|-------|-------|
| Method / URL | `GET /api/schema/` |
| Auth | None |
| Format | OpenAPI 3.0 YAML/JSON |
| Status | Implemented via `drf-spectacular` |

### API-DOCS — Swagger UI

| Field | Value |
|-------|-------|
| Method / URL | `GET /api/docs/` |
| Auth | None |
| Status | Implemented |

---

## 4. Authentication Endpoints

### API-AUTH-TOKEN — Obtain JWT Pair

| Field | Value |
|-------|-------|
| Method / URL | `POST /api/v1/auth/token/` |
| Auth | None |
| Status | Implemented |

**Request:**

```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| username | Required, string |
| password | Required, string |

**Response `200`:**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Errors:**

| Status | Condition |
|--------|-----------|
| 400 | Missing fields |
| 401 | Invalid credentials |

### API-AUTH-REFRESH — Refresh Access Token

| Field | Value |
|-------|-------|
| Method / URL | `POST /api/v1/auth/token/refresh/` |
| Auth | None (body carries refresh) |
| Status | Implemented |

**Request:**

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response `200`:**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## 5. Tenancy Endpoints

### API-ORG-LIST — List Organizations

| Field | Value |
|-------|-------|
| Method / URL | `GET /api/v1/organizations/` |
| Auth | JWT |
| Permissions | Authenticated; scoped to memberships |
| Status | Implemented |

**Response `200` (paginated):**

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "ACME Security Corp",
      "slug": "acme-security",
      "settings": {"retention_days": 90},
      "is_active": true,
      "created_at": "2026-07-17T06:00:00Z",
      "updated_at": "2026-07-17T06:00:00Z"
    }
  ]
}
```

### API-MEMBERSHIP-ME — Current User Memberships

| Field | Value |
|-------|-------|
| Method / URL | `GET /api/v1/memberships/me/` |
| Auth | JWT |
| Status | Implemented |

**Response `200`:**

```json
[
  {
    "organization": {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "ACME Security Corp",
      "slug": "acme-security",
      "settings": {"retention_days": 90},
      "is_active": true,
      "created_at": "2026-07-17T06:00:00Z",
      "updated_at": "2026-07-17T06:00:00Z"
    },
    "role": "owner"
  }
]
```

**Role enum:** `owner` | `admin` | `operator` | `viewer`

---

## 6. Dashboard

### API-DASH-SUMMARY — Overview Metrics

| Field | Value |
|-------|-------|
| Method / URL | `GET /api/v1/dashboard/summary/` |
| Auth | JWT |
| Status | Implemented |

**Response `200`:**

```json
{
  "cameras_total": 1,
  "cameras_online": 1,
  "events_today": 12,
  "events_pending_review": 5,
  "alerts_open": 2,
  "alerts_critical": 1,
  "edge_devices_online": 1,
  "edge_devices_total": 1
}
```

**Scoping:** Aggregates only resources in organizations where the user has membership.

---

## 7. Sites

### API-SITE-LIST — List / Create Sites

| Field | Value |
|-------|-------|
| Method / URL | `GET /api/v1/sites/` / `POST /api/v1/sites/` |
| Auth | JWT |
| GET permissions | Member of org |
| POST permissions | Owner or Admin of target organization |
| Status | Implemented |

**Query params (GET):**

| Param | Description |
|-------|-------------|
| search | Match `name`, `address` |
| ordering | `name`, `created_at` |

**POST request:**

```json
{
  "organization": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "Warehouse B",
  "address": "200 Industrial Rd",
  "timezone": "America/New_York",
  "is_active": true
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| organization | Required UUID; must exist; user must be Owner/Admin |
| name | Required; unique per organization |
| address | Optional string |
| timezone | Optional; default `UTC` |
| is_active | Optional boolean; default true |

**Response `201`:**

```json
{
  "id": "11111111-2222-3333-4444-555555555555",
  "organization": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "organization_name": "ACME Security Corp",
  "name": "Warehouse B",
  "address": "200 Industrial Rd",
  "timezone": "America/New_York",
  "is_active": true,
  "created_at": "2026-07-17T07:10:00Z",
  "updated_at": "2026-07-17T07:10:00Z"
}
```

**Errors:** `400` validation; `403` insufficient role; `401` unauthenticated.

### API-SITE-DETAIL — Retrieve / Update / Delete Site

| Field | Value |
|-------|-------|
| Method / URL | `GET|PATCH|DELETE /api/v1/sites/{id}/` |
| Auth | JWT |
| PATCH/DELETE | Owner or Admin |
| Status | Implemented |

**PATCH example:**

```json
{
  "address": "200 Industrial Rd, Suite 4",
  "is_active": false
}
```

---

## 8. Zones

### API-ZONE-LIST — List / Create Zones

| Field | Value |
|-------|-------|
| Method / URL | `GET /api/v1/zones/` / `POST /api/v1/zones/` |
| Auth | JWT |
| POST | Owner or Admin of site's organization |
| Status | Implemented |

**Query params:** `site`, `is_restricted`, `is_active`

**POST request:**

```json
{
  "site": "11111111-2222-3333-4444-555555555555",
  "name": "Loading Dock",
  "polygon_json": [[0.1, 0.2], [0.8, 0.2], [0.8, 0.9], [0.1, 0.9]],
  "is_restricted": true,
  "is_active": true
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| site | Required; must belong to user's org |
| name | Required; unique per site |
| polygon_json | Array of `[x,y]` pairs; preferably normalized 0–1 |
| is_restricted | Boolean |
| is_active | Boolean |

**Response `201`:** includes `id`, `site`, `site_name`, `organization`, zone fields, timestamps.

### API-ZONE-DETAIL — Retrieve / Update / Delete Zone

| Field | Value |
|-------|-------|
| Method / URL | `GET|PATCH|DELETE /api/v1/zones/{id}/` |
| PATCH/DELETE | Owner or Admin |
| Status | Implemented |

---

## 9. Cameras

### API-CAM-LIST — List / Create Cameras

| Field | Value |
|-------|-------|
| Method / URL | `GET /api/v1/cameras/` / `POST /api/v1/cameras/` |
| Auth | JWT |
| POST | Owner or Admin |
| Status | Implemented |

**Query params:** `site`, `status`, `is_active`, `search` (name)

**POST request:**

```json
{
  "site": "11111111-2222-3333-4444-555555555555",
  "zone": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "name": "Dock Camera 02",
  "rtsp_url": "rtsp://user:pass@192.168.1.50:554/stream1",
  "enabled_modules": ["multi_person_tracking", "intrusion_detection"],
  "metadata": {"vendor": "Hikvision", "resolution": "1080p"},
  "is_active": true
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| site | Required UUID |
| zone | Optional; **should** belong to same site (app validation Planned) |
| name | Required; unique per site |
| rtsp_url | Optional string (max 512) |
| enabled_modules | JSON array of module keys |
| status / last_seen_at | Read-only on create |

**Module keys:** `face_recognition`, `multi_person_tracking`, `activity_recognition`, `intrusion_detection`, `unknown_person`, `visitor_management`, `attendance`, `fire_smoke`, `weapon_detection`

**Response `201`:**

```json
{
  "id": "cccccccc-dddd-eeee-ffff-000000000001",
  "site": "11111111-2222-3333-4444-555555555555",
  "site_name": "Warehouse B",
  "organization": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "zone": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "zone_name": "Loading Dock",
  "name": "Dock Camera 02",
  "rtsp_url": "rtsp://user:pass@192.168.1.50:554/stream1",
  "status": "offline",
  "enabled_modules": ["multi_person_tracking", "intrusion_detection"],
  "last_seen_at": null,
  "metadata": {"vendor": "Hikvision", "resolution": "1080p"},
  "is_active": true,
  "created_at": "2026-07-17T07:20:00Z",
  "updated_at": "2026-07-17T07:20:00Z"
}
```

### API-CAM-DETAIL — Retrieve / Update / Delete Camera

| Field | Value |
|-------|-------|
| Method / URL | `GET|PATCH|DELETE /api/v1/cameras/{id}/` |
| PATCH/DELETE | Owner or Admin |
| Status | Implemented |

---

## 10. Edge Devices

### API-EDGE-DEV-LIST — List / Register Edge Device

| Field | Value |
|-------|-------|
| Method / URL | `GET /api/v1/edge-devices/` / `POST /api/v1/edge-devices/` |
| Auth | JWT |
| POST | Owner or Admin |
| Status | Implemented |

**POST request:**

```json
{
  "site": "11111111-2222-3333-4444-555555555555",
  "name": "Edge Node WH-B-01",
  "metadata": {"gpu": "RTX 3060"},
  "is_active": true
}
```

**Response `201` (api_key shown once):**

```json
{
  "id": "edge0001-0000-0000-0000-000000000001",
  "site": "11111111-2222-3333-4444-555555555555",
  "site_name": "Warehouse B",
  "organization": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "Edge Node WH-B-01",
  "status": "offline",
  "last_seen_at": null,
  "version": "",
  "metadata": {"gpu": "RTX 3060"},
  "is_active": true,
  "api_key_prefix": "AbCdEfGh",
  "api_key": "AbCdEfGhIjKlMnOpQrStUvWxYz0123456789_full",
  "created_at": "2026-07-17T07:25:00Z",
  "updated_at": "2026-07-17T07:25:00Z"
}
```

**Security notes:**
- Store `api_key` only on the edge node; never log it again.
- DB stores `api_key_hash` (SHA-256), not plaintext.
- Key rotation: Planned.

### API-EDGE-HEARTBEAT — Edge Heartbeat

| Field | Value |
|-------|-------|
| Method / URL | `POST /api/v1/edge/heartbeat/` |
| Auth | Edge API Key |
| Status | Implemented |

**Headers:**

```
X-Edge-API-Key: <raw_api_key>
Content-Type: application/json
```

**Request:**

```json
{
  "version": "0.1.0",
  "status": "online",
  "metadata": {"service": "edge-ai", "mode": "simulation"}
}
```

**Response `200`:**

```json
{
  "status": "ok",
  "registered": true,
  "device_id": "edge0001-0000-0000-0000-000000000001"
}
```

If key maps to no device: `{"status":"ok","registered":false}`.

**Side effects:** Updates `EdgeDevice.last_seen_at`, `status`, `version`; marks site cameras online.

### API-EDGE-CAM-LIST — Cameras for Edge Site

| Field | Value |
|-------|-------|
| Method / URL | `GET /api/v1/edge/cameras/` |
| Auth | Edge API Key |
| Status | Implemented |

**Response `200`:**

```json
{
  "results": [
    {
      "id": "cccccccc-dddd-eeee-ffff-000000000001",
      "name": "Dock Camera 02",
      "rtsp_url": "rtsp://...",
      "status": "online",
      "enabled_modules": ["multi_person_tracking"]
    }
  ]
}
```

Empty `results` if edge key is not bound to a device.

---

## 11. Detection Events

### API-EVT-LIST — List Events

| Field | Value |
|-------|-------|
| Method / URL | `GET /api/v1/events/` |
| Auth | JWT |
| Status | Implemented |

**Query params:**

| Param | Description |
|-------|-------------|
| camera | UUID filter |
| event_type | Enum filter |
| severity | `info` \| `warning` \| `critical` |
| review_status | `pending` \| `confirmed` \| `false_positive` \| `escalated` |
| search | camera name or edge_event_id |
| ordering | `created_at`, `confidence`, `severity` (prefix `-` for desc) |
| page | Page number |

**Response item:**

```json
{
  "id": "evt00001-0000-0000-0000-000000000001",
  "camera": "cccccccc-dddd-eeee-ffff-000000000001",
  "camera_name": "Dock Camera 02",
  "site_name": "Warehouse B",
  "organization": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "zone": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "event_type": "person_detected",
  "severity": "warning",
  "confidence": 0.87,
  "model_name": "yolo-sim",
  "model_version": "0.1.0",
  "payload": {"track_id": 1, "bbox": [100, 100, 200, 300]},
  "review_status": "pending",
  "reviewed_by": null,
  "reviewed_at": null,
  "edge_event_id": "edge-evt-abc-123",
  "created_at": "2026-07-17T07:30:00Z",
  "updated_at": "2026-07-17T07:30:00Z"
}
```

**Event type enum:**

`person_detected` | `face_recognized` | `unknown_person` | `intrusion` | `activity` | `fire_smoke` | `weapon` | `attendance` | `visitor`

### API-EVT-INGEST — Ingest Event (Edge)

| Field | Value |
|-------|-------|
| Method / URL | `POST /api/v1/events/ingest/` |
| Auth | Edge API Key |
| Status | Implemented |

**Request:**

```json
{
  "camera_id": "cccccccc-dddd-eeee-ffff-000000000001",
  "event_type": "person_detected",
  "severity": "warning",
  "confidence": 0.87,
  "model_name": "yolo-sim",
  "model_version": "0.1.0",
  "payload": {
    "track_id": 1,
    "bbox": [100, 100, 200, 300],
    "simulated": true
  },
  "zone_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "edge_event_id": "edge-evt-abc-123"
}
```

**Validation:**

| Field | Rules |
|-------|-------|
| camera_id | Required UUID; active camera |
| event_type | Required enum |
| severity | Optional enum; default `info` |
| confidence | Float 0.0–1.0 |
| model_name | Optional string ≤128 |
| model_version | Optional string ≤64 |
| payload | Optional object |
| zone_id | Optional UUID |
| edge_event_id | Optional; used for idempotency |

**Business rules:**
1. Camera must exist and `is_active=true`.
2. If edge user has bound device, camera.site must equal device.site → else `403`.
3. If `edge_event_id` matches existing → return `200` with existing event (idempotent).
4. On create → evaluate alert rules; may create `Alert` rows.
5. Updates camera `last_seen_at` and `status=online`.

**Responses:**

| Status | Meaning |
|--------|---------|
| 201 | New event created |
| 200 | Idempotent hit |
| 403 | Camera not on edge site |
| 404 | Camera not found |
| 400 | Validation failure |

**Remediation Planned:** Scope idempotency by organization; reject zone not belonging to camera.site; remove unbound global `EDGE_API_KEY` fallback for ingest.

### API-EVT-REVIEW — Review Event

| Field | Value |
|-------|-------|
| Method / URL | `GET|PATCH /api/v1/events/{id}/review/` |
| Auth | JWT |
| PATCH | Owner, Admin, or Operator |
| Status | Implemented |

**PATCH request:**

```json
{
  "review_status": "confirmed"
}
```

**Allowed values:** `pending` | `confirmed` | `false_positive` | `escalated`

**Side effects:** Sets `reviewed_by` = current user, `reviewed_at` = now.

---

## 12. Alerts

### API-ALERT-RULE-LIST — List / Create Alert Rules

| Field | Value |
|-------|-------|
| Method / URL | `GET /api/v1/alert-rules/` / `POST /api/v1/alert-rules/` |
| Auth | JWT |
| POST | Owner or Admin |
| Status | Implemented |

**Query params:** `event_type`, `is_active`

**POST request:**

```json
{
  "organization": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "Dock Intrusion Critical",
  "event_type": "intrusion",
  "min_severity": "critical",
  "min_confidence": 0.7,
  "is_active": true,
  "notify_email": true,
  "conditions": {"sites": ["11111111-2222-3333-4444-555555555555"]}
}
```

**Alert evaluation (Implemented):** For each active rule matching `event_type`, if event severity rank ≥ rule min_severity and confidence ≥ min_confidence → create Alert.

**Note:** `notify_email` and `conditions` are stored but not yet dispatched (notification service Planned).

### API-ALERT-LIST — List Alerts

| Field | Value |
|-------|-------|
| Method / URL | `GET /api/v1/alerts/` |
| Auth | JWT |
| Status | Implemented |

**Query params:** `status`, `severity`

**Response item:**

```json
{
  "id": "alert001-0000-0000-0000-000000000001",
  "organization": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "event": "evt00001-0000-0000-0000-000000000001",
  "event_type": "person_detected",
  "camera_name": "Dock Camera 02",
  "site_name": "Warehouse B",
  "rule": "rule0001-0000-0000-0000-000000000001",
  "title": "Person Detected — Dock Camera 02",
  "message": "Detection at Warehouse B with confidence 0.87",
  "severity": "warning",
  "status": "open",
  "acknowledged_by": null,
  "acknowledged_at": null,
  "resolved_at": null,
  "created_at": "2026-07-17T07:30:01Z",
  "updated_at": "2026-07-17T07:30:01Z"
}
```

### API-ALERT-ACK — Acknowledge / Resolve Alert

| Field | Value |
|-------|-------|
| Method / URL | `PATCH /api/v1/alerts/{id}/acknowledge/` |
| Auth | JWT |
| Permissions | Owner, Admin, Operator |
| Status | Implemented |

**Request:**

```json
{
  "status": "acknowledged"
}
```

**Allowed status values:** `open` | `acknowledged` | `resolved` | `dismissed`

**Side effects:**
- `acknowledged` → set `acknowledged_by`, `acknowledged_at`
- `resolved` or `dismissed` → set `resolved_at`

---

## 13. Audit Logs

### API-AUDIT-LIST — List Audit Logs

| Field | Value |
|-------|-------|
| Method / URL | `GET /api/v1/audit-logs/` |
| Auth | JWT |
| Status | Partial — endpoint Implemented; auto-write Planned |

**Query params:** `action`, `resource_type`

**Response item:**

```json
{
  "id": "aud00001-0000-0000-0000-000000000001",
  "organization": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "actor": 1,
  "actor_username": "admin",
  "action": "camera.create",
  "resource_type": "camera",
  "resource_id": "cccccccc-dddd-eeee-ffff-000000000001",
  "ip_address": "127.0.0.1",
  "details": {},
  "created_at": "2026-07-17T07:20:00Z"
}
```

---

## 14. Planned Endpoints (M3–M6)

### API-ATT-LIST — Attendance Records

`GET /api/v1/attendance/?person_id=&date_from=&date_to=` — JWT, HR+/Admin — Planned

### API-VIS-LIST — Visitors

`GET|POST /api/v1/visitors/` — JWT, HR+/Admin — Planned

### API-PERSON-ENROLL — Face Enrollment

`POST /api/v1/persons/{id}/enroll/` — JWT, Admin — multipart image + consent_id — Planned

### API-RPT-EXPORT — Report Export

`POST /api/v1/reports/export/` — JWT, Admin+ — `{type, date_from, date_to, format}` — Planned

### API-EVIDENCE-GET — Evidence Artifact

`GET /api/v1/evidence/{id}/` — JWT, Operator+ — signed URL to object storage — Planned

---

## 15. OpenAPI Generation

```bash
cd backend
python manage.py spectacular --file ../docs/openapi-schema.yml
```

Swagger UI: `http://localhost:8000/api/docs/`

**CI requirement:** Schema generation must succeed without import errors.

### 15.1 Example OpenAPI Path Fragment

```yaml
/api/v1/events/ingest/:
  post:
    operationId: events_ingest_create
    tags: [events]
    security:
      - EdgeApiKey: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/EventIngest'
    responses:
      '201':
        description: Created
      '200':
        description: Idempotent existing event
```

---

## 16. Client Integration Notes

| Client | Base | Auth |
|--------|------|------|
| React dashboard | `/api/v1` (proxied) | JWT access in `Authorization` |
| Edge service | `http://backend:8000/api/v1` | `X-Edge-API-Key` |
| External integrations | Public HTTPS base | JWT service account Planned |

**Frontend token storage (current):** access token in `localStorage` key `sv_access_token`. Refresh retry Planned.

---

## 17. Rate Limits (Planned)

| Client | Limit |
|--------|-------|
| User JWT | 100 req/min |
| Edge device | 1000 req/min |
| Ingest burst | 50 events/sec per edge |

---

## 18. Remediation Checklist for API Hardening

| ID | Issue | Target Fix |
|----|-------|------------|
| API-FIX-01 | Global `edge_event_id` idempotency | Unique per organization |
| API-FIX-02 | Unbound EDGE_API_KEY ingest | Require device-bound key |
| API-FIX-03 | Zone/site mismatch on camera/event | Serializer validation |
| API-FIX-04 | Inconsistent error envelope | Adopt standard error schema |
| API-FIX-05 | Audit not written on mutations | Call `log_audit` in views |
| API-FIX-06 | No rate limiting | Add DRF throttling classes |

---

## 19. Traceability

| API ID | Requirements | Use Cases | Tests |
|--------|--------------|-----------|-------|
| API-AUTH-TOKEN | UC-AUTH-01 | — | TEST-API-002 |
| API-CAM-LIST | FR-CAM-01 | UC-CAM-01 | TEST-API-003 |
| API-EVT-INGEST | FR-ALERT-01 | UC-EVT-01 | TEST-API-004,005 |
| API-EVT-REVIEW | US-02 | UC-EVT-02 | Planned |
| API-ALERT-ACK | FR-ALERT-04 | UC-ALERT-01 | Planned E2E |
| API-DASH-SUMMARY | FR-DASH-01 | — | TEST-API-006 |
