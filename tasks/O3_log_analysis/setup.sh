#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"
RUN_ID="$3"
mkdir -p "$REPORTS"
mkdir -p "$WORKSPACE/submission"

# Ensure PyYAML is available (needed by server.py)
python3 -c "import yaml" 2>/dev/null || pip3 install pyyaml -q

# Snapshot originals for diff grading
cp "$WORKSPACE/config/service.yaml" "$WORKSPACE/.service.yaml.orig" 2>/dev/null || true
cp "$WORKSPACE/src/server.py"       "$WORKSPACE/.server.py.orig"    2>/dev/null || true
