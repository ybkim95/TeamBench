#!/usr/bin/env bash
# Resume the 6 priority LB100 models on their *missing conditions only*.
# Primary provider per model; OpenRouter fallback has to be launched separately
# if the primary gets rate-limited (harness does NOT auto-fallback across providers).
#
# Resume dedupes on (condition:task_id:seed) — existing completed rows are skipped.
set -uo pipefail
cd "$(dirname "$0")/.."

PY=/u/ybkim95/TeamBench/venv/bin/python3
LOGS=logs
RESULTS=shared/ablation_results
TS=$(date +%Y%m%d_%H%M%S)
mkdir -p "$LOGS"

launch() {
    local short="$1"
    local model="$2"
    local conds="$3"
    local outfile="$4"
    local log="$LOGS/resume_${short}_${TS}.log"
    echo "[$short] model=$model  conds=[$conds]"
    echo "  out=$outfile"
    echo "  log=$log"
    nohup "$PY" -u scripts/run_leaderboard_100_ablation.py \
        --model "$model" \
        --seeds 0 \
        --conditions $conds \
        --output "$outfile" \
        > "$log" 2>&1 &
    echo "  PID=$!"
    sleep 5
}

# --- Gemini primary (rotates 13 keys on 429/503) ---
launch g3flash "gemini-3-flash-preview" \
    "team_no_verify team_no_plan" \
    "$RESULTS/lb100_g3flash_3cond_seed0.json"

launch g31lite "gemini-3.1-flash-lite-preview" \
    "team_no_verify" \
    "$RESULTS/lb100_g31lite_3cond_seed0.json"

# --- OpenAI primary (1 key, adapter backs off on 429) ---
launch gpt54 "gpt-5.4" \
    "team_no_verify" \
    "$RESULTS/lb100_gpt54_3cond_seed0.json"

launch gpt5nano "gpt-5.4-nano" \
    "team_no_verify" \
    "$RESULTS/lb100_gpt5nano_3cond_seed0.json"

# --- OpenRouter primary (openai/gpt-oss-* has no direct API; OR only) ---
launch gpt-oss-120b "openrouter:openai/gpt-oss-120b" \
    "restricted team_no_verify team_no_plan full" \
    "$RESULTS/lb100_gpt-oss-120b_seed0.json"

launch gpt-oss-20b "openrouter:openai/gpt-oss-20b" \
    "team_no_plan full" \
    "$RESULTS/lb100_gpt-oss-20b_seed0.json"

echo ""
echo "All 6 priority resumes launched. Monitor with:"
echo "  python3 scripts/lb100_status.py"
echo "  tail -f logs/resume_*_${TS}.log"
