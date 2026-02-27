#!/usr/bin/env bash
# EA Expertise-Asymmetry Experiment Runner
# N=30: 5 tasks × 6 seeds per condition per model
# Models: gemini-2.0-flash-lite, gemini-2.0-flash, gemini-2.5-flash
# Conditions: expertise_full, expertise_no_analysis, expertise_oracle
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON="$ROOT/venv/bin/python3"

# Load API key
set -a
source "$ROOT/.env"
set +a

EA_TASKS="EA1_security_scan EA2_coverage_gap EA3_type_safety EA4_code_quality EA5_dependency_audit"
SEEDS="0 1 2 3 4 5"
CONDITIONS="expertise_full expertise_no_analysis expertise_oracle"
MODELS="${MODELS:-gemini-2.0-flash-lite gemini-2.0-flash gemini-2.5-flash}"

OUTPUT_DIR="$ROOT/shared/ea_results"
mkdir -p "$OUTPUT_DIR"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

for MODEL in $MODELS; do
    SAFE_MODEL="${MODEL//\//_}"
    OUTPUT="$OUTPUT_DIR/${SAFE_MODEL}.json"
    LOG="$OUTPUT_DIR/${SAFE_MODEL}.log"

    if [ -f "$OUTPUT" ]; then
        log "Skipping $MODEL — output already exists: $OUTPUT"
        continue
    fi

    log "=== Starting model: $MODEL ==="
    log "Output: $OUTPUT"
    log "Log: $LOG"

    cd "$ROOT"
    PYTHONUNBUFFERED=1 "$PYTHON" -m harness.ablation \
        --model "$MODEL" \
        --tasks $EA_TASKS \
        --seeds $SEEDS \
        --conditions $CONDITIONS \
        --output "$OUTPUT" \
        --max-turns 20 \
        --max-remediation 1 \
        2>&1 | tee "$LOG"

    log "=== Finished model: $MODEL ==="
done

log "All models complete. Results in $OUTPUT_DIR/"
log "Files:"
ls -la "$OUTPUT_DIR/"
