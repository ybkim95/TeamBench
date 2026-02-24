#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$1"
REPORTS="$2"
RUN_ID="$3"

mkdir -p "$WORKSPACE/data"
printf 'alpha\nbeta\ngamma\n' > "$WORKSPACE/data/input.txt"
: > "$WORKSPACE/data/empty.txt"
mkdir -p "$REPORTS"
