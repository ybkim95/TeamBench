#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"
RUN_ID="$3"
mkdir -p "$REPORTS" "$WORKSPACE/tests"
# Install flask + requests so the server and tests can run
pip install flask requests pytest --quiet 2>/dev/null || true
