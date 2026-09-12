#!/usr/bin/env bash
# =============================================================================
#  TeamBench — Run 100-Task 5-Condition Ablation for ANY Model
# =============================================================================
#
#  Portable script — works on any GPU cluster. No hardcoded conda paths.
#  Supports API models (Gemini, OpenAI, Anthropic) and OSS models (via vLLM).
#
#  USAGE:
#    # --- API models (no GPU needed) ---
#    ./run_eval.sh api gemini-3.1-pro-preview
#    ./run_eval.sh api gpt-5-4
#    ./run_eval.sh api claude-sonnet-4-5
#
#    # --- OSS models (needs GPU + vLLM) ---
#    ./run_eval.sh oss qwen3-8b              # auto-detect GPUs
#    ./run_eval.sh oss qwen3-8b --gpus 0,1   # specify GPUs
#    ./run_eval.sh oss gemma3-27b --tp 2 --gpus 2,3
#
#    # --- Status ---
#    ./run_eval.sh status
#
#    # --- Re-grade existing runs (after grader fix) ---
#    ./run_eval.sh regrade <model-short-name>
#    ./run_eval.sh regrade --all
#
#  OUTPUTS (single source of truth):
#    shared/ablation_results/lb100_<model>_seed0.json              (final)
#    shared/ablation_results/lb100_<model>_seed0.json.checkpoint.jsonl  (resume)
#    logs/lb100_<model>_seed0.log                                  (log)
#
#  ENVIRONMENT VARIABLES (set in .env or export before running):
#    GEMINI_API_KEY      — for Gemini models
#    OPENAI_API_KEY      — for GPT models
#    ANTHROPIC_API_KEY   — for Claude models
#
#  PREREQUISITES:
#    pip install vllm     (for OSS models only)
#    pip install google-genai openai anthropic   (for API models)
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

RESULTS_DIR="shared/ablation_results"
LOGS_DIR="logs"
SEEDS="0"
VLLM_PORT=8000
mkdir -p "$RESULTS_DIR" "$LOGS_DIR"

# Load .env if present
[ -f .env ] && set -a && source .env && set +a

# ── Model registry ─────────────────────────────────────────────────────────
# OSS models: "short_name|HF_ID|TP|max_model_len"
declare -A OSS_MODELS=(
  # Small (1 GPU)
  [qwen35-0.8b]="Qwen/Qwen3.5-0.8B|1|32768"
  [qwen35-2b]="Qwen/Qwen3.5-2B|1|32768"
  [qwen3-4b]="Qwen/Qwen3-4B|1|32768"
  [qwen35-4b]="Qwen/Qwen3.5-4B|1|32768"
  [codegemma-7b]="google/codegemma-7b-it|1|8192"   # max_pos_embeddings=8192 in model config
  [qwen3-8b]="Qwen/Qwen3-8B|1|32768"
  [qwen35-9b]="Qwen/Qwen3.5-9B|1|32768"
  [qwen3-14b]="Qwen/Qwen3-14B|1|32768"
  [phi4-mini]="microsoft/Phi-4-mini-instruct|1|32768"
  [phi4]="microsoft/phi-4|1|32768"
  [glm4-9b]="THUDM/glm-4-9b-chat|1|32768"
  # Medium (1 GPU, 20-27B)
  [devstral-24b]="mistralai/Devstral-Small-2-24B-Instruct-2512|1|32768"
  # Large / MoE (2 GPUs)
  [qwen35-35b-a3b]="Qwen/Qwen3.5-35B-A3B|2|32768"
  [qwen3-coder-30b]="Qwen/Qwen3-Coder-30B-A3B-Instruct|2|32768"
  [qwen35-27b]="Qwen/Qwen3.5-27B|2|32768"
  [gemma3-27b]="google/gemma-3-27b-it|2|32768"
  [qwen25-coder-32b]="Qwen/Qwen2.5-Coder-32B-Instruct|2|32768"
  [deepseek-r1-32b]="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B|2|32768"
  [qwen3-32b]="Qwen/Qwen3-32B|2|32768"
)

# API models: "short_name|model_id"
declare -A API_MODELS=(
  [gemini-3.1-pro-preview]="gemini-3.1-pro-preview"
  [gemini-3-pro-preview]="gemini-3-pro-preview"
  [gemini-3-flash-preview]="gemini-3-flash-preview"
  [gemini-3.1-lite-preview]="gemini-3.1-lite-preview"
  [gemini-2.5-pro]="gemini-2.5-pro"
  [gemini-2.5-flash]="gemini-2.5-flash"
  [gpt-5-4]="gpt-5-4"
  [gpt-5-nano]="gpt-5-nano"
  [gpt-5-mini]="gpt-5-mini"
  [gpt-5.3-chat]="gpt-5.3-chat"
  [claude-sonnet-4-5]="claude-sonnet-4-5"
  [claude-opus-4-6]="claude-opus-4-6"
  [claude-haiku-4-5]="claude-haiku-4-5"
)

# ── Helper functions ───────────────────────────────────────────────────────

usage() {
    sed -n '/^#  USAGE:/,/^# ====/p' "$0" | sed 's/^#  \?//'
}

die() { echo "ERROR: $*" >&2; exit 1; }

outfile() { echo "$RESULTS_DIR/lb100_${1}_seed${SEEDS}.json"; }
logfile() { echo "$LOGS_DIR/lb100_${1}_seed${SEEDS}.log"; }

check_done() {
    local out; out=$(outfile "$1")
    [ -f "$out" ] && echo "Already complete: $out" && return 0
    return 1
}

wait_for_server() {
    local port="$1" pid="$2" max_wait="${3:-5400}"  # 90 min for slow NFS loads
    local elapsed=0
    while [ $elapsed -lt $max_wait ]; do
        if curl -s -m 2 "http://localhost:${port}/v1/models" > /dev/null 2>&1; then
            echo "  vLLM server ready (${elapsed}s)"
            return 0
        fi
        if ! kill -0 "$pid" 2>/dev/null; then
            echo "  ERROR: vLLM server crashed"
            return 1
        fi
        sleep 10
        elapsed=$((elapsed + 10))
    done
    echo "  ERROR: vLLM server timeout (${max_wait}s)"
    return 1
}

stop_server() {
    local pid="$1"
    [ -n "$pid" ] && kill "$pid" 2>/dev/null
    sleep 2
    [ -n "$pid" ] && kill -9 "$pid" 2>/dev/null
}

# ── Commands ───────────────────────────────────────────────────────────────

cmd_status() {
    python3 scripts/lb100_status.py
}

cmd_api() {
    local short="$1"
    local model_id="${API_MODELS[$short]:-}"
    [ -z "$model_id" ] && die "Unknown API model: $short. Available: ${!API_MODELS[*]}"
    check_done "$short" && return 0

    local out; out=$(outfile "$short")
    local log; log=$(logfile "$short")
    echo "═══════════════════════════════════════════════════════════════"
    echo "  API model: $model_id"
    echo "  Output:    $out"
    echo "  Log:       $log"
    echo "═══════════════════════════════════════════════════════════════"

    PYTHONUNBUFFERED=1 python3 scripts/run_leaderboard_100_ablation.py \
        --model "$model_id" \
        --seeds $SEEDS \
        --output "$out" \
        2>&1 | tee "$log"
}

cmd_oss() {
    local short="$1"; shift
    local spec="${OSS_MODELS[$short]:-}"
    [ -z "$spec" ] && die "Unknown OSS model: $short. Available: ${!OSS_MODELS[*]}"
    check_done "$short" && return 0

    # Parse spec
    IFS='|' read -r HF_ID TP MAX_LEN <<< "$spec"

    # Parse optional flags
    local GPUS="" GPU_UTIL="0.70" PARSER="hermes" DTYPE="bfloat16" PORT="$VLLM_PORT"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --gpus)      GPUS="$2"; shift 2 ;;
            --tp)        TP="$2"; shift 2 ;;
            --port)      PORT="$2"; shift 2 ;;
            --gpu-util)  GPU_UTIL="$2"; shift 2 ;;
            --parser)    PARSER="$2"; shift 2 ;;
            --dtype)     DTYPE="$2"; shift 2 ;;
            --max-len)   MAX_LEN="$2"; shift 2 ;;
            *) die "Unknown flag: $1" ;;
        esac
    done

    # Auto-detect GPUs if not specified
    if [ -z "$GPUS" ]; then
        local ngpu; ngpu=$(nvidia-smi -L 2>/dev/null | wc -l)
        if [ "$TP" -eq 1 ]; then
            GPUS="0"
        elif [ "$TP" -eq 2 ]; then
            GPUS="0,1"
        elif [ "$TP" -eq 4 ]; then
            GPUS="0,1,2,3"
        else
            GPUS=$(seq -s, 0 $((TP - 1)))
        fi
    fi

    local out; out=$(outfile "$short")
    local log; log=$(logfile "$short")
    local server_log="$LOGS_DIR/vllm_${short}.log"

    echo "═══════════════════════════════════════════════════════════════"
    echo "  OSS model:  $short ($HF_ID)"
    echo "  TP=$TP  GPUs=$GPUS  Port=$PORT  MaxLen=$MAX_LEN"
    echo "  Output:     $out"
    echo "  Log:        $log"
    echo "  Server log: $server_log"
    echo "═══════════════════════════════════════════════════════════════"

    # Start vLLM server
    echo "  Starting vLLM server..."
    CUDA_VISIBLE_DEVICES="$GPUS" python -m vllm.entrypoints.openai.api_server \
        --model "$HF_ID" \
        --port "$PORT" \
        --trust-remote-code \
        --enable-auto-tool-choice \
        --tool-call-parser "$PARSER" \
        --max-model-len "$MAX_LEN" \
        --gpu-memory-utilization "$GPU_UTIL" \
        --dtype "$DTYPE" \
        --tensor-parallel-size "$TP" \
        --enforce-eager > "$server_log" 2>&1 &
    local SERVER_PID=$!

    wait_for_server "$PORT" "$SERVER_PID" || { stop_server "$SERVER_PID"; return 1; }

    # Run ablation
    PYTHONUNBUFFERED=1 python3 scripts/run_leaderboard_100_ablation.py \
        --model "vllm:${HF_ID}@http://localhost:${PORT}/v1" \
        --seeds $SEEDS \
        --output "$out" \
        2>&1 | tee "$log"

    echo "  Evaluation finished."
    stop_server "$SERVER_PID"
}

cmd_regrade() {
    if [ "$1" = "--all" ]; then
        python3 scripts/regrade_runs.py --all
    else
        python3 scripts/regrade_runs.py --model "$1"
    fi
}

cmd_list() {
    echo "API models:"
    for m in $(echo "${!API_MODELS[@]}" | tr ' ' '\n' | sort); do
        local out; out=$(outfile "$m")
        local status="❌"
        [ -f "$out" ] && status="✅"
        [ -f "${out}.checkpoint.jsonl" ] && [ ! -f "$out" ] && status="⏳"
        printf "  %s %-30s %s\n" "$status" "$m" "${API_MODELS[$m]}"
    done
    echo ""
    echo "OSS models:"
    for m in $(echo "${!OSS_MODELS[@]}" | tr ' ' '\n' | sort); do
        local out; out=$(outfile "$m")
        local status="❌"
        [ -f "$out" ] && status="✅"
        [ -f "${out}.checkpoint.jsonl" ] && [ ! -f "$out" ] && status="⏳"
        IFS='|' read -r hf tp ml <<< "${OSS_MODELS[$m]}"
        printf "  %s %-25s TP=%s  %s\n" "$status" "$m" "$tp" "$hf"
    done
}

# ── Main ───────────────────────────────────────────────────────────────────

case "${1:-help}" in
    status)   cmd_status ;;
    list)     cmd_list ;;
    api)      shift; cmd_api "${1:?Usage: ./run_eval.sh api <model>}" ;;
    oss)      shift; cmd_oss "$@" ;;
    regrade)  shift; cmd_regrade "${1:?Usage: ./run_eval.sh regrade <model|--all>}" ;;
    help|-h|--help) usage ;;
    *) echo "Unknown command: $1"; usage; exit 1 ;;
esac
