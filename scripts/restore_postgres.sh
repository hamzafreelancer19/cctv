#!/usr/bin/env bash
# Restore a PostgreSQL custom-format dump.
set -euo pipefail

DUMP_FILE="${1:-}"
if [[ -z "$DUMP_FILE" ]]; then
  echo "Usage: $0 <dump-file>"
  exit 1
fi

DATABASE_URL="${DATABASE_URL:-postgres://sentinel:sentinel@localhost:5432/sentinelvision}"
echo "Restoring $DUMP_FILE → $DATABASE_URL"
pg_restore --clean --if-exists -d "$DATABASE_URL" "$DUMP_FILE"
echo "Restore complete. Validate apps via /api/v1/ready/ (RTO target ≤ 1h)."
