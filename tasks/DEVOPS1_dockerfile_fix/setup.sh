#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"
RUN_ID="$3"

chmod +x "$WORKSPACE/test_build.sh" 2>/dev/null || true
mkdir -p "$REPORTS"
