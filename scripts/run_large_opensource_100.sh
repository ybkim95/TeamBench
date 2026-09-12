#!/usr/bin/env bash
# Run LARGE open-source models (27B+) on the 100-task leaderboard set.
# These need TP=2 (2 GPUs) to fit in memory.
#
# Usage: nohup bash scripts/run_large_opensource_100.sh > logs/large_opensource_100.log 2>&1 &

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
    local LOG_SERVER="logs/vllm_${SHORT_NAME}_v2.log"
    local LOG_EVAL="logs/eval_${SHORT_NAME}_v2.log"

    echo ""
    echo "================================================================"
    echo "  MODEL: $SHORT_NAME ($HF_ID)"
    echo "  Port=$PORT TP=$TP Parser=$PARSER GPUs=$GPUS MaxLen=$MAX_LEN"
    echo "  $(date)"
    echo "================================================================"

    # Check if already completed
    local CKPT_FILES=$(find "$CAMPAIGN_DIR" -name 'checkpoint.jsonl' 2>/dev/null)
    for ckpt in $CKPT_FILES; do
        local DONE=$(wc -l < "$ckpt")
        if [ "$DONE" -ge 100 ]; then
            echo "  Already complete ($DONE runs). Skipping."
            return 0
        fi
    done

    # Kill any leftover GPU processes
    fuser /dev/nvidia0 /dev/nvidia1 /dev/nvidia2 /dev/nvidia3 2>/dev/null | xargs -r kill -9 2>/dev/null
    sleep 3

    # Start vLLM server
    echo "  Starting vLLM server..."
    CUDA_VISIBLE_DEVICES="$GPUS" python -m vllm.entrypoints.openai.api_server \
        --model "$HF_ID" \
        --port "$PORT" \
        --trust-remote-code \
        --enable-auto-tool-choice \
        --tool-call-parser "$PARSER" \
        --max-model-len "$MAX_LEN" \
        --gpu-memory-utilization 0.85 \
        --dtype "$DTYPE" \
        --tensor-parallel-size "$TP" \
        --enforce-eager $EXTRA > "$LOG_SERVER" 2>&1 &
    local SERVER_PID=$!
    echo "  Server PID: $SERVER_PID"

    # Wait for server (up to 15 min for large models)
    echo "  Waiting for server..."
    for i in $(seq 1 90); do
        if curl -s -m 2 "http://localhost:$PORT/v1/models" > /dev/null 2>&1; then
            echo "  Server ready after $((i*10))s"
            break
        fi
        if ! kill -0 $SERVER_PID 2>/dev/null; then
            echo "  ERROR: Server crashed. Check $LOG_SERVER"
            tail -5 "$LOG_SERVER"
            return 1
        fi
        sleep 10
    done

    if ! curl -s -m 3 "http://localhost:$PORT/v1/models" > /dev/null 2>&1; then
        echo "  ERROR: Server never started. Killing."
        kill $SERVER_PID 2>/dev/null; kill -9 $SERVER_PID 2>/dev/null
        return 1
    fi

    # Run evaluation
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
    sleep 3
    kill -9 $SERVER_PID 2>/dev/null
    wait $SERVER_PID 2>/dev/null
    echo "  Server stopped."
}

echo "========================================"
echo "  Large Open-Source Models (27B+)"
echo "  $(date)"
echo "========================================"

# --- 27B models: TP=2, GPUs 0,1 ---

run_model "Qwen/Qwen3.5-27B" \
    "qwen35-27b" 8000 2 "hermes" "bfloat16" 8192 "0,1"

run_model "google/gemma-3-27b-it" \
    "gemma3-27b" 8000 2 "hermes" "bfloat16" 8192 "0,1"

# --- 30-35B MoE models: fit on 1 GPU (active params < 5B) ---

run_model "Qwen/Qwen3.5-35B-A3B" \
    "qwen35-35b-a3b" 8000 1 "hermes" "bfloat16" 8192 "0"

run_model "Qwen/Qwen3-Coder-30B-A3B-Instruct" \
    "qwen3-coder-30b" 8000 1 "hermes" "bfloat16" 8192 "0"

# --- 32B dense models: TP=2, GPUs 0,1 ---

run_model "Qwen/Qwen2.5-Coder-32B-Instruct" \
    "qwen25-coder-32b" 8000 2 "hermes" "bfloat16" 8192 "0,1"

run_model "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B" \
    "deepseek-r1-32b" 8000 2 "hermes" "bfloat16" 8192 "0,1"

# --- Gemma 4: Skip if transformers too old ---
echo ""
echo "  NOTE: Gemma 4 requires newer transformers. Checking..."
python -c "import transformers; v=transformers.__version__; print(f'transformers={v}')" 2>&1
# Only attempt if transformers >= 4.46
python -c "
import transformers
v = tuple(int(x) for x in transformers.__version__.split('.')[:2])
exit(0 if v >= (4, 46) else 1)
" 2>/dev/null
if [ $? -eq 0 ]; then
    run_model "google/gemma-4-26B-A4B-it" \
        "gemma4-26b" 8000 1 "hermes" "auto" 8192 "0"
else
    echo "  Skipping Gemma 4 (transformers too old)"
fi

echo ""
echo "========================================"
echo "  ALL LARGE MODELS COMPLETE"
echo "  $(date)"
echo "========================================"
