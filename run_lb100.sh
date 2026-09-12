#!/usr/bin/env bash
# =============================================================================
#  TeamBench — 100-Task Leaderboard Ablation (5-condition)
# =============================================================================
#
#  ONE entrypoint for reproducing the 100-task ablation across ALL models.
#  All outputs go to a single directory. One file per (model, seed) pair.
#
#  USAGE:
#    ./run_lb100.sh                      # list models + status
#    ./run_lb100.sh status               # same as default
#    ./run_lb100.sh api <short_name>     # run ONE API model (gemini/gpt/claude)
#    ./run_lb100.sh oss <short_name>     # run ONE OSS (vLLM) model
#    ./run_lb100.sh all-oss              # run ALL OSS models sequentially
#    ./run_lb100.sh all-api              # run ALL API models sequentially
#
#  OUTPUT LOCATION  (single source of truth):
#    shared/ablation_results/lb100_<short_name>_seed<N>.json          (final)
#    shared/ablation_results/lb100_<short_name>_seed<N>.json.checkpoint.jsonl  (in-progress, auto-resume)
#
#  LOGS:
#    logs/lb100_<short_name>_seed<N>.log
#
#  CONDITIONS (5):  oracle, restricted, team_no_verify, team_no_plan, full
#  TASKS (100):     leaderboard/data/leaderboard_100_tasks.json
#  TOTAL per model: 5 x 100 x N_seeds = 500 runs per seed
# =============================================================================

set -o pipefail
cd "$(dirname "$0")"

RESULTS_DIR="shared/ablation_results"
LOGS_DIR="logs"
SEEDS="0"
mkdir -p "$RESULTS_DIR" "$LOGS_DIR"

# --- API MODELS (no vLLM server needed) ---
# Format: "short_name|model_id"
API_MODELS=(
  "gemini-3.1-pro-preview|gemini-3.1-pro-preview"
  "gemini-3-pro-preview|gemini-3-pro-preview"
  "gemini-3-flash-preview|gemini-3-flash-preview"
  "gemini-2.5-pro|gemini-2.5-pro"
  "gemini-2.5-flash|gemini-2.5-flash"
  "gpt-5-4|gpt-5-4"
  "gpt-5-nano|gpt-5-nano"
  "claude-sonnet-4-5|claude-sonnet-4-5"
  "claude-opus-4-6|claude-opus-4-6"
  "claude-haiku-4-5|claude-haiku-4-5"
)

# --- OSS MODELS (via vLLM; must be in run_all_opensource_100_ablation.sh) ---
OSS_MODELS=(
  "qwen35-0.8b"
  "qwen35-2b"
  "qwen3-4b"
  "qwen35-4b"
  "codegemma-7b"
  "qwen3-8b"
  "qwen35-9b"
  "qwen3-14b"
  "devstral-24b"
  "qwen35-35b-a3b"
  "qwen3-coder-30b"
  "qwen35-27b"
  "gemma3-27b"
  "qwen25-coder-32b"
  "deepseek-r1-32b"
  "phi4-mini"
  "phi4"
  "glm4-9b"
  "qwen3-32b"
)

usage() {
  grep -E '^#' "$0" | sed 's/^# \{0,1\}//' | head -30
}

status() {
  python3 scripts/lb100_status.py
}

run_api() {
  local short="$1"
  local model_id="$1"
  # Look up model_id from table
  for entry in "${API_MODELS[@]}"; do
    IFS='|' read -r s m <<< "$entry"
    if [[ "$s" == "$short" ]]; then model_id="$m"; fi
  done
  local out="$RESULTS_DIR/lb100_${short}_seed0.json"
  local log="$LOGS_DIR/lb100_${short}_seed0.log"
  echo "[API] model=$model_id  seeds=$SEEDS"
  echo "  output: $out"
  echo "  log:    $log"
  nohup python3 -u scripts/run_leaderboard_100_ablation.py \
      --model "$model_id" \
      --seeds $SEEDS \
      --output "$out" \
      > "$log" 2>&1 &
  echo "  PID=$!"
}

run_oss() {
  local short="$1"
  echo "[OSS] single-model runs go through the vLLM orchestrator."
  echo "To run one OSS model, edit scripts/run_all_opensource_100_ablation.sh"
  echo "and comment out all other run_model lines, OR run the full batch:"
  echo "    ./run_lb100.sh all-oss"
}

run_all_oss() {
  local log="$LOGS_DIR/lb100_all_oss_$(date +%Y%m%d_%H%M).log"
  echo "[OSS-ALL] launching vLLM orchestrator for all ${#OSS_MODELS[@]} models"
  echo "  log: $log"
  echo "  outputs: $RESULTS_DIR/lb100_<short>_seed0.json"
  nohup bash scripts/run_all_opensource_100_ablation.sh > "$log" 2>&1 &
  echo "  PID=$!"
}

run_all_api() {
  echo "[API-ALL] launching ${#API_MODELS[@]} API models in parallel"
  for entry in "${API_MODELS[@]}"; do
    IFS='|' read -r short model_id <<< "$entry"
    local out="$RESULTS_DIR/lb100_${short}_seed0.json"
    if [[ -f "$out" ]]; then
      echo "  [skip] $short (output exists)"
      continue
    fi
    run_api "$short"
    sleep 2
  done
}

case "${1:-status}" in
  status|"")     status ;;
  help|-h|--help) usage ;;
  api)           shift; run_api "${1:?usage: api <short_name>}" ;;
  oss)           shift; run_oss "${1:?usage: oss <short_name>}" ;;
  all-oss)       run_all_oss ;;
  all-api)       run_all_api ;;
  *)             echo "Unknown command: $1"; usage; exit 1 ;;
esac
