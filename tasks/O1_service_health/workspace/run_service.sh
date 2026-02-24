#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="${REPORTS_DIR:-../reports}/service.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Start the service and redirect stdout/stderr to logs
python server.py >"$LOG_FILE" 2>&1
