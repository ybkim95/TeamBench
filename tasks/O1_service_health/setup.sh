#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"
RUN_ID="$3"

chmod +x "$WORKSPACE/run_service.sh"
mkdir -p "$REPORTS"
