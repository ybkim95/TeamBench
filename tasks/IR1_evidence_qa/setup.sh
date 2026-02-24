#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"
RUN_ID="$3"

mkdir -p "$WORKSPACE/corpus" "$REPORTS"
cp "$(dirname "$0")/corpus/"* "$WORKSPACE/corpus/"
