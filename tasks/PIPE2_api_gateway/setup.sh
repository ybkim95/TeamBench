#!/usr/bin/env bash
# Setup script for PIPE2_api_gateway.
# When parameterized generation is active, the harness calls the generator
# and this script is a no-op placeholder.
# For static (legacy) mode, this script would write fixture files to $WORKSPACE.
#
# Args: $1=WORKSPACE $2=REPORTS $3=RUN_ID
set -euo pipefail
WORKSPACE="$1"
REPORTS="${2:-}"
RUN_ID="${3:-}"

mkdir -p "$WORKSPACE"
if [ -n "$REPORTS" ]; then
  mkdir -p "$REPORTS"
fi

# No static fixtures — all files are produced by gen_pipe2_api_gateway.py at runtime.
echo "PIPE2_api_gateway setup complete (parameterized mode)."
