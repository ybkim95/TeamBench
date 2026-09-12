#!/bin/bash
# Launch ablation with the correct venv
# Usage: ./scripts/launch_ablation.sh <model> <output_file> [extra_args...]
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

source venv/bin/activate

MODEL="$1"
OUTPUT="$2"
shift 2

echo "Launching ablation for $MODEL -> $OUTPUT (extra: $@)"
exec python scripts/run_leaderboard_100_ablation.py \
    --model "$MODEL" --seeds 0 --conditions oracle full \
    --output "$OUTPUT" "$@"
