#!/usr/bin/env bash
# Launch all API model resumes after the harness fix (2026-04-19).
# Each runs in background and writes to its own log.
set -uo pipefail
cd "$(dirname "$0")/.."

mkdir -p logs

stagger=0

launch() {
    local short="$1"
    local model="$2"
    local conds="$3"
    local outfile="$4"
    local log="logs/resume_${short}_$(date +%Y%m%d_%H%M%S).log"
    echo "[$short] model=$model conds=[$conds] log=$log"
    sleep "$stagger"
    nohup /u/ybkim95/TeamBench/venv/bin/python3 scripts/run_leaderboard_100_ablation.py \
        --model "$model" \
        --seeds 0 \
        --conditions $conds \
        --output "$outfile" \
        > "$log" 2>&1 &
    echo "  PID=$!"
    stagger=$((stagger + 5))
}

# Anthropic: full 3-cond rerun (restricted+team_no_plan+team_no_verify)
launch haiku45 "claude-haiku-4-5-20251001" "restricted team_no_plan team_no_verify" \
    "shared/ablation_results/lb100_haiku45_3cond_seed0.json"

launch sonnet46 "claude-sonnet-4-6" "restricted team_no_plan team_no_verify" \
    "shared/ablation_results/lb100_sonnet46_3cond_seed0.json"

# OpenAI
launch gpt54 "gpt-5.4" "restricted team_no_plan team_no_verify" \
    "shared/ablation_results/lb100_gpt54_3cond_seed0.json"

launch gpt5nano "gpt-5.4-nano" "restricted team_no_plan team_no_verify" \
    "shared/ablation_results/lb100_gpt5nano_3cond_seed0.json"

# Gemini
launch g31lite "gemini-3.1-flash-lite-preview" "restricted team_no_plan team_no_verify" \
    "shared/ablation_results/lb100_g31lite_3cond_seed0.json"

launch g3flash "gemini-3-flash-preview" "restricted team_no_plan team_no_verify" \
    "shared/ablation_results/lb100_g3flash_3cond_seed0.json"

# Gemini-3.1-pro: only restricted needs rerun (other 4 conditions intact in checkpoint)
launch gemini-3.1-pro-preview "gemini-3.1-pro-preview" "restricted" \
    "shared/ablation_results/lb100_gemini-3.1-pro-preview_seed0.json"

# Haiku45 oraclefull: needs 29 missing full runs to finish (oracle 100/100, full 71/100)
launch haiku45_full_continue "claude-haiku-4-5-20251001" "full" \
    "shared/ablation_results/lb100_haiku45_oraclefull_seed0.json"

echo ""
echo "All resumes launched. Check progress with:"
echo "  python scripts/lb100_status.py"
