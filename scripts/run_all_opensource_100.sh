#!/usr/bin/env bash
# Run ALL open-source models on the 100-task leaderboard set.
# Sequential: serve model -> evaluate -> kill -> next model.
#
# Usage: nohup bash scripts/run_all_opensource_100.sh > logs/opensource_100.log 2>&1 &
#
# GPU setup: 3x A40 (46GB each), uses tensor parallelism as needed.
# Models are run one at a time to avoid GPU memory conflicts.

set -o pipefail
cd "$(dirname "$0")/.."

CONDA_BASE="/u/ybkim95/zhiyuan/miniconda3"
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate vllm-qwen
export PYTHONNOUSERSITE=1

TASKS_FILE="leaderboard/data/100_task_ids.txt"
CAMPAIGN_BASE="shared/campaigns/opensource_100"
mkdir -p "$CAMPAIGN_BASE" logs

TASKS=$(cat "$TASKS_FILE" | tr '\n' ' ')

run_model() {
    local HF_ID="$1"
    local SHORT_NAME="$2"
    local PORT="$3"
    local TP="$4"
    local PARSER="$5"
    local DTYPE="$6"
    local MAX_LEN="$7"
    local GPUS="$8"
    local EXTRA="${9:-}"

    local CAMPAIGN_DIR="$CAMPAIGN_BASE/${SHORT_NAME}"
    local LOG_SERVER="logs/vllm_${SHORT_NAME}.log"
    local LOG_EVAL="logs/eval_${SHORT_NAME}.log"

    echo ""
    echo "================================================================"
    echo "  MODEL: $SHORT_NAME ($HF_ID)"
    echo "  Port=$PORT TP=$TP Parser=$PARSER GPUs=$GPUS MaxLen=$MAX_LEN"
    echo "  Campaign: $CAMPAIGN_DIR"
    echo "  $(date)"
    echo "================================================================"

    # Check if already completed
    local CKPT="$CAMPAIGN_DIR/checkpoint.jsonl"
    if [ -f "$CKPT" ]; then
        local DONE=$(wc -l < "$CKPT")
        echo "  Checkpoint has $DONE runs. Using --resume."
        if [ "$DONE" -ge 100 ]; then
            echo "  Already complete ($DONE runs). Skipping."
            return 0
        fi
    fi

    # Start vLLM server
    echo "  Starting vLLM server..."
    CUDA_VISIBLE_DEVICES="$GPUS" python -m vllm.entrypoints.openai.api_server \
        --model "$HF_ID" \
        --port "$PORT" \
        --trust-remote-code \
        --enable-auto-tool-choice \
        --tool-call-parser "$PARSER" \
        --max-model-len "$MAX_LEN" \
        --gpu-memory-utilization 0.90 \
        --dtype "$DTYPE" \
        --tensor-parallel-size "$TP" \
        --enforce-eager $EXTRA > "$LOG_SERVER" 2>&1 &
    local SERVER_PID=$!
    echo "  Server PID: $SERVER_PID"

    # Wait for server (up to 10 min)
    echo "  Waiting for server..."
    for i in $(seq 1 60); do
        if curl -s -m 2 "http://localhost:$PORT/v1/models" > /dev/null 2>&1; then
            echo "  Server ready after $((i*10))s"
            break
        fi
        if ! kill -0 $SERVER_PID 2>/dev/null; then
            echo "  ERROR: Server crashed. Check $LOG_SERVER"
            return 1
        fi
        sleep 10
    done

    if ! curl -s -m 3 "http://localhost:$PORT/v1/models" > /dev/null 2>&1; then
        echo "  ERROR: Server never started. Killing."
        kill $SERVER_PID 2>/dev/null; kill -9 $SERVER_PID 2>/dev/null
        return 1
    fi

    # Run evaluation using batch_runner
    echo "  Starting evaluation on 100 tasks..."
    VLLM_BASE_URL="http://localhost:$PORT/v1" \
    PYTHONUNBUFFERED=1 python3 -m harness.batch_runner \
        --models "$HF_ID" \
        --tasks $TASKS \
        --seeds 0 \
        --campaign-dir "$CAMPAIGN_DIR" \
        --max-turns 15 \
        --max-remediation 0 \
        --resume \
        2>&1 | tee "$LOG_EVAL"

    echo "  Evaluation finished."

    # Kill server
    echo "  Stopping server..."
    kill $SERVER_PID 2>/dev/null
    sleep 5
    kill -9 $SERVER_PID 2>/dev/null
    wait $SERVER_PID 2>/dev/null
    echo "  Server stopped."
}

echo "========================================"
echo "  TeamBench 100-Task Open-Source Eval"
echo "  $(date)"
echo "  Models: 16 open-source"
echo "  Tasks: 100"
echo "========================================"

# --- Small models (fit on 1 GPU, ~8-16GB) ---

run_model "Qwen/Qwen3.5-0.8B" \
    "qwen35-0.8b" 8000 1 "hermes" "bfloat16" 8192 "0"

run_model "Qwen/Qwen3.5-2B" \
    "qwen35-2b" 8000 1 "hermes" "bfloat16" 8192 "0"

run_model "Qwen/Qwen3-4B" \
    "qwen3-4b" 8000 1 "hermes" "bfloat16" 8192 "0"

run_model "Qwen/Qwen3.5-4B" \
    "qwen35-4b" 8000 1 "hermes" "bfloat16" 8192 "0"

run_model "google/codegemma-7b-it" \
    "codegemma-7b" 8000 1 "hermes" "bfloat16" 8192 "0"

run_model "Qwen/Qwen3-8B" \
    "qwen3-8b" 8000 1 "hermes" "bfloat16" 8192 "0"

run_model "Qwen/Qwen3.5-9B" \
    "qwen35-9b" 8000 1 "hermes" "bfloat16" 8192 "0"

run_model "Qwen/Qwen3-14B" \
    "qwen3-14b" 8000 1 "hermes" "bfloat16" 8192 "0"

# --- Medium models (1 GPU, ~20-30GB) ---

run_model "mistralai/Devstral-Small-2-24B-Instruct-2512" \
    "devstral-24b" 8000 1 "mistral" "bfloat16" 8192 "0"

run_model "Qwen/Qwen3.5-27B" \
    "qwen35-27b" 8000 1 "hermes" "bfloat16" 8192 "0"

run_model "google/gemma-3-27b-it" \
    "gemma3-27b" 8000 1 "hermes" "bfloat16" 8192 "0"

run_model "google/gemma-4-26B-A4B-it" \
    "gemma4-26b" 8000 1 "hermes" "auto" 8192 "0"

# --- Large models (2 GPUs, TP=2, ~32-35B) ---

run_model "Qwen/Qwen2.5-Coder-32B-Instruct" \
    "qwen25-coder-32b" 8000 2 "hermes" "bfloat16" 8192 "0,1"

run_model "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B" \
    "deepseek-r1-32b" 8000 2 "hermes" "bfloat16" 8192 "0,1"

run_model "Qwen/Qwen3.5-35B-A3B" \
    "qwen35-35b-a3b" 8000 1 "hermes" "bfloat16" 8192 "0"

run_model "Qwen/Qwen3-Coder-30B-A3B-Instruct" \
    "qwen3-coder-30b" 8000 1 "hermes" "bfloat16" 8192 "0"

echo ""
echo "========================================"
echo "  ALL MODELS COMPLETE"
echo "  $(date)"
echo "========================================"
