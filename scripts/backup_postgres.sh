#!/usr/bin/env bash
# PostgreSQL logical backup (base for PITR when WAL archiving is enabled).
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR"

DATABASE_URL="${DATABASE_URL:-postgres://sentinel:sentinel@localhost:5432/sentinelvision}"

echo "Backing up PostgreSQL to ${BACKUP_DIR}/pg_${TIMESTAMP}.dump"
pg_dump "$DATABASE_URL" -Fc -f "${BACKUP_DIR}/pg_${TIMESTAMP}.dump"

# Retain 7 days of dumps by default
find "$BACKUP_DIR" -name 'pg_*.dump' -mtime +7 -delete 2>/dev/null || true
echo "Done. RPO target ≤ 15m requires continuous WAL archiving in production."
