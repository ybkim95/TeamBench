#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"
RUN_ID="$3"

mkdir -p "$WORKSPACE/output" "$REPORTS"

# Initialise the SQLite database from seed_data.sql
if [ -f "$WORKSPACE/seed_data.sql" ]; then
    sqlite3 "$WORKSPACE/retention.db" < "$WORKSPACE/seed_data.sql"
fi
