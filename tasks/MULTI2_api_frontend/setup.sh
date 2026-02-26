#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"
RUN_ID="$3"
SEED="${4:-0}"
echo "MULTI2_api_frontend setup complete (seed=$SEED)"
