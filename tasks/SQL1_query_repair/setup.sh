#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"
RUN_ID="$3"
SEED="${4:-0}"

cd "$WORKSPACE"
python3 setup_db.py
echo "SQL1_query_repair setup complete (seed=$SEED)"
