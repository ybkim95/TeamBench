#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"
RUN_ID="$3"
mkdir -p "$REPORTS"
# Save original for diff size check
cp "$WORKSPACE/server.py" "$WORKSPACE/.server.py.orig"
