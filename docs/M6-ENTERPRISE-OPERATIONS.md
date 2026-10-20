# M6 — Enterprise Operations Roadmap

**Status:** M6.1–M6.8 implemented as production-oriented workstreams (adapters/providers configurable; vendor SDKs may remain pending where noted).

## Architecture overview

```text
DetectionEvent
      │
      ▼
Post-ingest hooks (alerts → m4 → m5 → notifications → audit → recording → siem → metrics)
      │
      ├─ NotificationJob ──► Celery (notifications) ──► Email/SMS/WhatsApp/Push/Webhook
      │                         │ retry / DLQ / delivery logs / rate limits
      ├─ RecordingJob ─────► Celery (recordings) ──► RecordingAdapter (RTSP / vendor)
      ├─ SIEMForwardJob ───► Celery (siem) ──► Splunk/Sentinel/QRadar/Elastic/Syslog/Webhook
      └─ SnapshotObject ◄── Upload API ◄── Edge ──► Local / MinIO / S3 (signed URL)
```

---

## M6.1 — Notification Service

| Capability | Implementation |
|------------|----------------|
| Celery workers | `apps.ops.tasks.send_notification_job` |
| Retry + backoff | Exponential delay; `FAILED` → re-drain |
| Dead letter | `status=dead` after `max_attempts` |
| Channels | email, sms, whatsapp, push, webhook (`apps.ops.notifications.channels`) |
| Rate limiting | `NOTIFICATION_RATE_LIMIT_PER_MINUTE` per org/channel/destination |
| Delivery logs | `NotificationDeliveryLog` |

APIs: `GET /api/v1/notifications/`, `GET /api/v1/notifications/logs/`

Compose: `celery_worker`, `celery_beat`, `redis`

---

## M6.2 — Evidence Storage

Flow: Edge → `POST /api/v1/snapshots/upload/` → MinIO/S3/local → signed URL → dashboard

Metadata on `SnapshotObject`:

- `checksum`, `mime_type`, `width`, `height`, `expires_at`, `uploaded_by_edge`, `storage_backend`

Backends: `EVIDENCE_STORAGE_BACKEND=local|minio|s3`  
Module: `apps.ops.storage.evidence`

---

## M6.3 — Recording Integrations

Interface: `RecordingAdapter` (`start_recording` / `stop_recording` / `fetch_clip`)

| Vendor | Status |
|--------|--------|
| Generic RTSP | OpenCV clip capture when available |
| ONVIF / Hikvision / Dahua / Milestone / Axis | Adapter interface + SDK-pending stubs |
| Stub | Dev fallback |

API: `GET /api/v1/recordings/`  
Org setting: `recording_vendor`

---

## M6.4 — Enterprise Identity

| Feature | Status |
|---------|--------|
| SSO provider config (OIDC / SAML / LDAP) | `SSOProvider` + `GET/POST /api/v1/sso/providers/` |
| Azure AD / Okta / Google | Via OIDC issuer URLs in provider settings |
| MFA flag | `SSOProvider.mfa_required`, `SessionPolicy.mfa_required` |
| Password policies | `GET/PUT /api/v1/identity/password-policy/` |
| Session management | `GET/PUT /api/v1/identity/session-policy/` |
| SCIM | Flag `scim_enabled` (future provisioning) |

Full IdP handshake libraries are configuration-ready; wire production IdP clients per deployment.

---

## M6.5 — Observability

Metrics endpoint: `GET /api/v1/metrics/` (Prometheus)

Gauges/counters: `camera_online`, `notification_queue_depth`, `event_rate`, ingest totals, notification sent/failures

Probes: `GET /api/v1/ready/`, `GET /api/v1/live/` (+ existing `/api/v1/health/`)

Configs: `deploy/prometheus/prometheus.yml`, `deploy/grafana/sentinelvision-overview.json`

---

## M6.6 — High Availability

Recommended topology:

```text
NGINX → API pods → PostgreSQL primary (+ read replica) → Redis → Celery workers
```

Compose ships Redis + Celery for horizontal worker scale. Production HA adds:

- Multiple API replicas + rolling updates
- PG primary/replica + automatic failover
- Health probes (`/ready/`, `/live/`)
- Zero-downtime deploys via rolling restart

---

## M6.7 — SIEM Integrations

Targets: Splunk, Microsoft Sentinel, IBM QRadar, Elastic Security, Syslog, generic webhook

Org setting example:

```json
{
  "siem_targets": [
    {"target": "webhook", "destination": "https://siem.example/hooks"},
    {"target": "syslog", "destination": "siem-host:514"}
  ]
}
```

API: `GET /api/v1/siem/jobs/`

---

## M6.8 — Backup & Disaster Recovery

Scripts:

- `scripts/backup_postgres.sh` — `pg_dump` retention
- `scripts/restore_postgres.sh` — `pg_restore`

Objectives:

| Metric | Target |
|--------|--------|
| RPO | ≤ 15 minutes (enable WAL archiving / PITR in prod) |
| RTO | ≤ 1 hour |

Also plan: object storage lifecycle, snapshot retention (`expires_at`), configuration backup.

---

## Production readiness checklist

| Item | Status |
|------|--------|
| Unified ingest + idempotency | ✅ |
| Zone validation | ✅ |
| AI modules M2–M5 | ✅ |
| Notification workers | ✅ (providers stubbed when URLs empty) |
| Evidence S3/MinIO + signed URLs | ✅ |
| Real NVR adapters | 🟡 RTSP live; vendor SDKs pending |
| SSO (OIDC/SAML) config | ✅ (handshake libs per deploy) |
| Monitoring + alerting | ✅ Prometheus metrics + Grafana stub |
| Centralized logging | 🟡 app logging; Loki/ELK optional |
| Backup & DR scripts | ✅ |
| Load / endurance testing | ☐ |
| Security testing (OWASP, deps, pentest) | ☐ |

**v1.0 GA gate:** complete yellow/unchecked items for the target deployment environment.
