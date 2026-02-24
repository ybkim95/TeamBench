#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"
RUN_ID="$3"
SEED="${4:-0}"
echo "MULTI1_fullstack_fix setup complete (seed=$SEED)"
