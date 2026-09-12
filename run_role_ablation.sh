#!/usr/bin/env bash
# Role ablation launcher: 27 configs × 25 tasks × 1 seed across 3 model families.
#
# Models: Anthropic Haiku 4.5, Google Gemini-3-flash, OpenAI GPT-5.4-mini
# Output: shared/role_ablation/
#
# Usage:
#   ./run_role_ablation.sh --smoke        # 3 configs × 2 tasks, <$2, ~5-10 min
#   ./run_role_ablation.sh --estimate     # project full-run cost from smoke data
#   ./run_role_ablation.sh --full         # full 27×25 campaign
#   ./run_role_ablation.sh --resume       # continue after interruption
#   ./run_role_ablation.sh --config PAEGVO  # single config across all 25 tasks
#   ./run_role_ablation.sh --aggregate    # rebuild aggregate JSON/LaTeX
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Prefer the repo-local venv that has anthropic/openai/google-genai installed.
if [[ -z "${PYTHON:-}" ]]; then
    if [[ -x "$SCRIPT_DIR/venv/bin/python" ]]; then
        PY="$SCRIPT_DIR/venv/bin/python"
    elif [[ -x "$SCRIPT_DIR/.venv/bin/python" ]]; then
        PY="$SCRIPT_DIR/.venv/bin/python"
    else
        PY="python3"
    fi
else
    PY="$PYTHON"
fi
echo "Python: $PY"
ROLE_DIR="shared/role_ablation"
LOG_ROOT="$ROLE_DIR/logs"

# -----------------------------------------------------------------------------
# Pre-flight checks
# -----------------------------------------------------------------------------
preflight() {
    echo "=== Pre-flight checks ==="
    local ok=1

    # Tasks file
    if [[ ! -f "$ROLE_DIR/tasks_25.json" ]]; then
        echo "  [.] Generating 25-task list..."
        "$PY" scripts/select_role_ablation_tasks.py >/dev/null
        echo "  [OK] tasks_25.json created"
    else
        echo "  [OK] tasks_25.json exists"
    fi

    # Pricing file
    if [[ ! -f "$ROLE_DIR/pricing.json" ]]; then
        echo "  [!!] $ROLE_DIR/pricing.json MISSING"
        ok=0
    else
        echo "  [OK] pricing.json exists"
    fi

    # API keys (check any source: env or .env files)
    local anthropic_ok=0 google_ok=0 openai_ok=0
    [[ -n "${ANTHROPIC_API_KEY:-}" ]] && anthropic_ok=1
    [[ -n "${GOOGLE_API_KEY:-}${GEMINI_API_KEY:-}" ]] && google_ok=1
    [[ -n "${OPENAI_API_KEY:-}" ]] && openai_ok=1
    # Also check .env files that adapters read from
    for envfile in .env "$HOME/CoDaS_v4/.env" "$HOME/.env"; do
        [[ -f "$envfile" ]] || continue
        grep -q "^ANTHROPIC_API_KEY=" "$envfile" 2>/dev/null && anthropic_ok=1 || true
        grep -qE "^(GOOGLE|GEMINI)_API_KEY=" "$envfile" 2>/dev/null && google_ok=1 || true
        grep -q "^OPENAI_API_KEY=" "$envfile" 2>/dev/null && openai_ok=1 || true
    done
    [[ $anthropic_ok -eq 1 ]] && echo "  [OK] Anthropic API key found" || { echo "  [!!] ANTHROPIC_API_KEY missing"; ok=0; }
    [[ $google_ok -eq 1 ]]    && echo "  [OK] Google API key found"    || { echo "  [!!] GOOGLE/GEMINI_API_KEY missing"; ok=0; }
    [[ $openai_ok -eq 1 ]]    && echo "  [OK] OpenAI API key found"    || { echo "  [!!] OPENAI_API_KEY missing"; ok=0; }

    # Disk space (need at least 5 GB for full run)
    local avail_kb
    avail_kb=$(df -k . | awk 'NR==2 {print $4}')
    local avail_gb=$((avail_kb / 1024 / 1024))
    if (( avail_gb < 5 )); then
        echo "  [!!] Low disk: ${avail_gb}GB available (recommend >5GB)"
    else
        echo "  [OK] Disk: ${avail_gb}GB available"
    fi

    [[ $ok -eq 1 ]] || { echo "Pre-flight failed. Fix the [!!] items above."; exit 1; }
    echo
}

# -----------------------------------------------------------------------------
# Post-run summary
# -----------------------------------------------------------------------------
summary() {
    local summary_file="$ROLE_DIR/results/summary.json"
    local cost_file="$ROLE_DIR/cost_tracking.json"
    [[ -f "$summary_file" ]] || { echo "No summary yet."; return; }
    echo
    echo "=== Post-run summary ==="
    "$PY" -c "
import json
s = json.load(open('$summary_file'))
c = json.load(open('$cost_file')) if __import__('os').path.exists('$cost_file') else {}
print(f'  total runs: {s.get(\"total_runs\", 0)}')
print(f'  configs with data: {s.get(\"configs_completed\", 0)}')
print(f'  total cost: \${s.get(\"total_cost_usd\", 0):.4f}')
print(f'  total tokens: in={c.get(\"total_input_tokens\", 0):,}  out={c.get(\"total_output_tokens\", 0):,}')
print()
print('  Top configs by pass rate:')
for i, cfg in enumerate(s.get('top_configs', [])[:5], 1):
    print(f'    {i}. {cfg[\"config\"]}: {cfg[\"success_rate\"]*100:.1f}% '
          f'({cfg[\"passes\"]}/{cfg[\"total_runs\"]}) '
          f'cost=\${cfg[\"total_cost_usd\"]:.2f}')
"
}

# -----------------------------------------------------------------------------
# Mode dispatch
# -----------------------------------------------------------------------------
MODE="${1:-}"
shift || true

case "$MODE" in
    --smoke)
        preflight
        TS=$(date -u +%Y%m%dT%H%M%SZ)
        LOG="$LOG_ROOT/smoke_$TS.log"
        mkdir -p "$LOG_ROOT"
        echo "=== Smoke test: 3 configs × 2 tasks, max_turns=5 ==="
        echo "Driver log: $LOG"
        "$PY" scripts/run_role_ablation.py --smoke "$@" 2>&1 | tee "$LOG"
        summary
        echo
        echo "Next: ./run_role_ablation.sh --estimate"
        ;;
    --estimate)
        echo "=== Projected full-run cost (based on smoke data) ==="
        "$PY" scripts/run_role_ablation.py --estimate "$@"
        echo
        echo "If the projection is acceptable, run: ./run_role_ablation.sh --full"
        ;;
    --full)
        preflight
        TS=$(date -u +%Y%m%dT%H%M%SZ)
        LOG="$LOG_ROOT/full_$TS.log"
        mkdir -p "$LOG_ROOT"
        echo "=== Full campaign: 27 configs × 25 tasks × 1 seed ==="
        echo "Driver log: $LOG"
        "$PY" scripts/run_role_ablation.py --full "$@" 2>&1 | tee "$LOG"
        summary
        ;;
    --resume)
        preflight
        TS=$(date -u +%Y%m%dT%H%M%SZ)
        LOG="$LOG_ROOT/resume_$TS.log"
        mkdir -p "$LOG_ROOT"
        echo "=== Resuming campaign (skipping runs already in per_run.jsonl) ==="
        echo "Driver log: $LOG"
        "$PY" scripts/run_role_ablation.py --full --resume "$@" 2>&1 | tee "$LOG"
        summary
        ;;
    --config)
        preflight
        CFG="${1:?--config requires a name, e.g. PAEGVO}"
        shift || true
        TS=$(date -u +%Y%m%dT%H%M%SZ)
        LOG="$LOG_ROOT/${CFG}_$TS.log"
        mkdir -p "$LOG_ROOT"
        echo "=== Single config: $CFG ==="
        "$PY" scripts/run_role_ablation.py --full --config "$CFG" "$@" 2>&1 | tee "$LOG"
        summary
        ;;
    --aggregate)
        "$PY" scripts/run_role_ablation.py --aggregate
        summary
        ;;
    --help|-h|"")
        grep -E "^# " "$0" | sed 's/^# //'
        ;;
    *)
        echo "Unknown mode: $MODE" >&2
        echo "Use --help for usage." >&2
        exit 2
        ;;
esac
