#!/usr/bin/env bash
# Setup for D4: Data Validation Pipeline
# Args: $1=WORKSPACE $2=REPORTS $3=RUN_ID
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"

mkdir -p "$WORKSPACE/data/input" "$WORKSPACE/data/output" "$WORKSPACE/config" "$REPORTS"
