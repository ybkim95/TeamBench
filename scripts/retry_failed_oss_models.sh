#!/usr/bin/env bash
# Retry the 5 models that failed in the main OSS batch.
# MoE models: now TP=2 (was TP=1 → OOM)
# Dense 27B+: TP=2, try with --disable-custom-all-reduce to work around Triton issue

set -o pipefail
cd "$(dirname "$0")/.."

CONDA_BASE="/u/ybkim95/zhiyuan/miniconda3"
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate vllm-qwen
export PYTHONNOUSERSITE=1

mkdir -p logs shared/ablation_results

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

    local OUTFILE="shared/ablation_results/lb100_${SHORT_NAME}_seed0.json"
    local LOG_SERVER="logs/vllm_${SHORT_NAME}_retry.log"

    echo ""
    echo "================================================================"
    echo "  RETRY: $SHORT_NAME ($HF_ID)"
    echo "  Port=$PORT TP=$TP Parser=$PARSER GPUs=$GPUS"
    echo "  Output: $OUTFILE"
    echo "  $(date)"
    echo "================================================================"

    if [ -f "$OUTFILE" ]; then
        echo "  Output exists. Skipping."
        return 0
    fi

    # Kill leftover GPU processes
    for g in $(echo "$GPUS" | tr ',' ' '); do
        fuser /dev/nvidia$g 2>/dev/null | tr ' ' '\n' | grep -v '^$' | xargs -r kill -9 2>/dev/null
    done
    sleep 5

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
        --enforce-eager \
        --disable-custom-all-reduce $EXTRA > "$LOG_SERVER" 2>&1 &
    local SERVER_PID=$!

    echo "  Waiting for server (up to 40 min)..."
    for i in $(seq 1 240); do
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

    echo "  Starting 5-condition ablation on 100 tasks..."
    PYTHONUNBUFFERED=1 python3 scripts/run_leaderboard_100_ablation.py \
        --model "vllm:${HF_ID}@http://localhost:${PORT}/v1" \
        --seeds 0 \
        --output "$OUTFILE" \
        2>&1 | tee "logs/eval_${SHORT_NAME}_retry.log"

    echo "  Evaluation finished."
    kill $SERVER_PID 2>/dev/null
    sleep 3
    kill -9 $SERVER_PID 2>/dev/null
    wait $SERVER_PID 2>/dev/null
    echo "  Server stopped."
}

echo "========================================"
echo "  RETRY: Failed OSS Models"
echo "  $(date)"
echo "========================================"

# MoE models — now TP=2 (was TP=1 → OOM)
run_model "Qwen/Qwen3.5-35B-A3B" "qwen35-35b-a3b" 8000 2 "hermes" "bfloat16" 8192 "0,1"
run_model "Qwen/Qwen3-Coder-30B-A3B-Instruct" "qwen3-coder-30b" 8000 2 "hermes" "bfloat16" 8192 "0,1"

# Dense 27B+ — TP=2 with --disable-custom-all-reduce
run_model "Qwen/Qwen3.5-27B" "qwen35-27b" 8000 2 "hermes" "bfloat16" 8192 "0,1"
run_model "google/gemma-3-27b-it" "gemma3-27b" 8000 2 "hermes" "bfloat16" 8192 "0,1"
run_model "Qwen/Qwen2.5-Coder-32B-Instruct" "qwen25-coder-32b" 8000 2 "hermes" "bfloat16" 8192 "0,1"

echo ""
echo "========================================"
echo "  RETRY COMPLETE — $(date)"
echo "========================================"
