#!/bin/bash
# Run open-source models sequentially: serve -> evaluate -> kill -> next
# Usage: bash scripts/run_opensource_sequential.sh

set -o pipefail

CONDA_BASE="/u/ybkim95/zhiyuan/miniconda3"
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate vllm-qwen

# CRITICAL: Disable user site-packages to avoid version conflicts
export PYTHONNOUSERSITE=1
cd /u/ybkim95/TeamBench

TASKS_DIR="tasks"
RESULTS_DIR="shared/ablation_results"

run_model() {
    local MODEL_ID="$1"
    local PORT="$2"
    local TP="$3"
    local PARSER="$4"
    local DTYPE="$5"
    local MAX_LEN="$6"
    local OUTPUT_NAME="$7"
    local GPUS="$8"
    local EXTRA_ARGS="${9}"

    echo ""
    echo "================================================================"
    echo "  MODEL: $MODEL_ID"
    echo "  Port: $PORT | TP: $TP | Parser: $PARSER | MaxLen: $MAX_LEN"
    echo "  Output: $OUTPUT_NAME"
    echo "================================================================"

    # Check if results already exist
    if [ -f "$RESULTS_DIR/$OUTPUT_NAME" ]; then
        echo "  Results already exist, skipping."
        return 0
    fi

    # Start vLLM server
    local LOG_FILE="logs/$(echo $OUTPUT_NAME | sed 's/.json//').log"
    echo "  Starting vLLM server..."
    CUDA_VISIBLE_DEVICES="$GPUS" python -m vllm.entrypoints.openai.api_server \
        --model "$MODEL_ID" \
        --port "$PORT" \
        --trust-remote-code \
        --enable-auto-tool-choice \
        --tool-call-parser "$PARSER" \
        --max-model-len "$MAX_LEN" \
        --gpu-memory-utilization 0.90 \
        --dtype "$DTYPE" \
        --tensor-parallel-size "$TP" \
        --enforce-eager $EXTRA_ARGS > "$LOG_FILE" 2>&1 &
    local SERVER_PID=$!
    echo "  Server PID: $SERVER_PID"

    # Wait for server to be ready (up to 30 min for large model downloads + loading)
    echo "  Waiting for server to start (up to 30 min)..."
    for i in $(seq 1 180); do
        if curl -s -m 2 "http://localhost:$PORT/v1/models" > /dev/null 2>&1; then
            echo "  Server ready after ${i}0 seconds!"
            break
        fi
        # Check if error occurred in log
        if grep -q "Error\|OOM\|OutOfMemory\|not divisible" "$LOG_FILE" 2>/dev/null; then
            if ! curl -s -m 2 "http://localhost:$PORT/v1/models" > /dev/null 2>&1; then
                echo "  ERROR: Server failed. Check $LOG_FILE"
                return 1
            fi
        fi
        sleep 10
    done

    # Verify server is actually responding
    if ! curl -s -m 5 "http://localhost:$PORT/v1/models" > /dev/null 2>&1; then
        echo "  ERROR: Server never became ready. Killing and skipping."
        kill $SERVER_PID 2>/dev/null; kill -9 $SERVER_PID 2>/dev/null
        wait $SERVER_PID 2>/dev/null
        return 1
    fi

    # Run evaluation
    echo "  Starting evaluation..."
    python3 scripts/run_opensource_v2.py \
        --model "$(echo $OUTPUT_NAME | sed 's/crossmodel_//;s/_seed0.json//')" \
        --api-base "http://localhost:$PORT/v1" 2>&1 | tee "logs/eval_$(echo $OUTPUT_NAME | sed 's/.json//').log"

    local EVAL_EXIT=$?
    echo "  Evaluation finished with exit code: $EVAL_EXIT"

    # Kill server
    echo "  Stopping server..."
    kill $SERVER_PID 2>/dev/null
    sleep 5
    kill -9 $SERVER_PID 2>/dev/null
    wait $SERVER_PID 2>/dev/null
    sleep 5

    # Verify GPUs are free
    echo "  GPU memory after cleanup:"
    nvidia-smi --query-gpu=index,memory.used --format=csv,noheader

    return $EVAL_EXIT
}

echo "Starting sequential open-source evaluation"
echo "Date: $(date)"
echo ""

# 1. Llama 4 Scout FP8 (Meta, MoE 109B/17B active)
run_model "RedHatAI/Llama-4-Scout-17B-16E-Instruct-FP8-dynamic" \
    8000 4 "llama3_json" "auto" 16384 \
    "crossmodel_llama4_scout_seed0.json" "0,1,2,3"

# 2. DeepSeek-R1-Distill-Llama-70B (DeepSeek, 70B dense)
run_model "deepseek-ai/DeepSeek-R1-Distill-Llama-70B" \
    8000 4 "hermes" "bfloat16" 16384 \
    "crossmodel_deepseek_r1_llama70b_seed0.json" "0,1,2,3"

# 3. Gemma 3 27B (Google, 27B dense)
run_model "google/gemma-3-27b-it" \
    8000 1 "hermes" "bfloat16" 16384 \
    "crossmodel_gemma3_27b_seed0.json" "0"

# 4. Devstral 2 AWQ-4bit (Mistral, 123B dense quantized)
run_model "cyankiwi/Devstral-2-123B-Instruct-2512-AWQ-4bit" \
    8000 4 "mistral" "auto" 8192 \
    "crossmodel_devstral2_123b_seed0.json" "0,1,2,3" \
    "--quantization awq"

echo ""
echo "================================================================"
echo "  ALL DONE"
echo "  $(date)"
echo "================================================================"
