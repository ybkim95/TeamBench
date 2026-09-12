#!/usr/bin/env bash
# 03b_resume.sh.
# Resume the two stalled providers (gemini_3_flash and claude_haiku_4_5)
# and skip gpt_5_4_mini (already finalized).
# Resume is automatic via results_<cond>.json.checkpoint.jsonl in the harness.
#
# Slices needed (per the audit on 2026-04-25 14:49 UTC):
#   gemini_3_flash    : enforced (resume +20)  +  enforced_shared_history (full 50)
#   claude_haiku_4_5  : enforced_shared_history (resume +29)

set -euo pipefail
EXP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$EXP_DIR/../.." && pwd)"

cd "$REPO_ROOT"

if [[ -x "$REPO_ROOT/venv/bin/python3" ]]; then
    export PATH="$REPO_ROOT/venv/bin:$PATH"
fi
if [[ -f "$REPO_ROOT/.env" ]]; then
    set -a; source "$REPO_ROOT/.env"; set +a
fi
: "${OPENROUTER_API:?OPENROUTER_API missing}"

SELECTION="$EXP_DIR/config/task_selection.json"
LOG_DIR="$EXP_DIR/logs"
RUNS_DIR="$EXP_DIR/runs"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$LOG_DIR" "$RUNS_DIR"

TASKS="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(" ".join(d["selected_flat"]))' "$SELECTION")"
[[ -z "$TASKS" ]] && { echo "[resume] empty task list"; exit 2; }

SEEDS="0 1"

echo "[resume] tasks: $TASKS"
echo "[resume] timestamp tag: $TS"

run_slice() {
    local name="$1"; local slug="$2"; local cond="$3"
    local mlog="$LOG_DIR/${name}_${cond}_resume_${TS}.log"
    local out="$RUNS_DIR/$name/results_${cond}.json"
    {
        echo "[$(date -u +%H:%M:%S)] resume $name :: $cond -> $out"
        python3 -m harness.ablation \
            --model "$slug" \
            --tasks $TASKS \
            --seeds $SEEDS \
            --conditions "$cond" \
            --output "$out" \
            --max-turns 20 \
            --max-remediation 2
        echo "[$(date -u +%H:%M:%S)] done $name :: $cond"
    } >>"$mlog" 2>&1
}

# gemini_3_flash: finish enforced, then run enforced_shared_history
run_gemini() {
    run_slice gemini_3_flash openrouter:google/gemini-3-flash-preview enforced
    run_slice gemini_3_flash openrouter:google/gemini-3-flash-preview enforced_shared_history
}

# claude_haiku_4_5: only enforced_shared_history
run_haiku() {
    run_slice claude_haiku_4_5 openrouter:anthropic/claude-haiku-4.5 enforced_shared_history
}

PIDS=()
echo "[resume] launching gemini_3_flash slice chain"
( run_gemini ) &
PIDS+=("$!")
echo "[resume] launching claude_haiku_4_5 slice"
( run_haiku ) &
PIDS+=("$!")

EXIT=0
for pid in "${PIDS[@]}"; do
    if ! wait "$pid"; then
        echo "[resume] worker $pid failed" >&2
        EXIT=1
    fi
done

echo "[resume] all workers exited; status=$EXIT"
exit "$EXIT"
