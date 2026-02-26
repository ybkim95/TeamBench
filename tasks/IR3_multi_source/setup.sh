#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"
RUN_ID="$3"

# Copy corpus into workspace so Executor can access it
mkdir -p "$WORKSPACE/corpus"
cp -r "$(dirname "$0")/corpus/"* "$WORKSPACE/corpus/"
mkdir -p "$REPORTS"
