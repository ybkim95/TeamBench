#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"
RUN_ID="$3"

mkdir -p "$WORKSPACE/output" "$REPORTS"

# Install Flask if not available
python3 -c "import flask" 2>/dev/null || pip install flask --quiet
