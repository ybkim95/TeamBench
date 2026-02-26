#!/usr/bin/env bash
# Setup script for SEC6_csrf_protection
# Installs Python dependencies for the workspace.
set -euo pipefail

WORKSPACE="$1"

cd "$WORKSPACE"
pip install -q -r requirements.txt
