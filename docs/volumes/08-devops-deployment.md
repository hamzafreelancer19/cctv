---
volume: 08
title: DevOps and Deployment
status: draft
---

# DevOps and Deployment

> **SentinelVision AI — Enterprise Documentation Suite**
> Status legend: Implemented | Planned | Future


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
