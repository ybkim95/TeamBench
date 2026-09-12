#!/usr/bin/env bash
# Launch batch 1 vLLM servers: Phi-4-mini, Phi-4, Mistral Small 3.2, GLM-4-9B
#
# GPU allocation:
#   GPU 0 -> Phi-4-mini (3.8B, port 8010, ~8GB)
#   GPU 1 -> Phi-4 (14B, port 8011, ~28GB)
#   GPU 2 -> Mistral Small 3.2 (24B, port 8012, ~46GB)
#   GPU 3 -> GLM-4-9B-Chat (9B, port 8013, ~18GB)
#
# Usage:
#   bash scripts/launch_batch1_vllm.sh           # Launch all
#   bash scripts/launch_batch1_vllm.sh stop       # Stop all
#   bash scripts/launch_batch1_vllm.sh status     # Check status

set -euo pipefail
cd "$(dirname "$0")/.."

SESSIONS=(
    "vllm-phi4mini:microsoft/Phi-4-mini-instruct:0:8010"
    "vllm-phi4:microsoft/phi-4:1:8011"
    "vllm-mistral32:mistralai/Mistral-Small-3.2-24B-Instruct-2506:2:8012"
    "vllm-glm4:THUDM/glm-4-9b-chat:3:8013"
)

# Tool call parsers per model
declare -A PARSERS=(
    ["microsoft/Phi-4-mini-instruct"]="hermes"
    ["microsoft/phi-4"]="hermes"
    ["mistralai/Mistral-Small-3.2-24B-Instruct-2506"]="mistral"
    ["THUDM/glm-4-9b-chat"]="hermes"
)

if [ "${1:-}" = "stop" ]; then
    echo "Stopping batch 1 servers..."
    for entry in "${SESSIONS[@]}"; do
        IFS=':' read -r sess model gpu port <<< "$entry"
        tmux kill-session -t "$sess" 2>/dev/null && echo "  Stopped $sess" || echo "  $sess not running"
    done
    exit 0
fi

if [ "${1:-}" = "status" ]; then
    echo "Batch 1 vLLM server status:"
    for entry in "${SESSIONS[@]}"; do
        IFS=':' read -r sess model gpu port <<< "$entry"
        if tmux has-session -t "$sess" 2>/dev/null; then
            if curl -s --max-time 2 "http://localhost:$port/v1/models" >/dev/null 2>&1; then
                echo "  ✓ $model (port $port) — READY"
            else
                echo "  ⏳ $model (port $port) — loading..."
            fi
        else
            echo "  ✗ $model (port $port) — not running"
        fi
    done
    exit 0
fi

# Default: launch all
VLLM_PYTHON="/u/ybkim95/zhiyuan/miniconda3/envs/vllm-qwen/bin/python"
echo "Launching batch 1 (4 models on 4 GPUs)..."
echo ""

for entry in "${SESSIONS[@]}"; do
    IFS=':' read -r sess model gpu port <<< "$entry"
    parser="${PARSERS[$model]}"
    tmux kill-session -t "$sess" 2>/dev/null || true
    tmux new-session -d -s "$sess" \
        "CUDA_VISIBLE_DEVICES=$gpu $VLLM_PYTHON -m vllm.entrypoints.openai.api_server \
            --model $model \
            --port $port \
            --trust-remote-code \
            --enable-auto-tool-choice \
            --tool-call-parser $parser \
            --max-model-len 32768 \
            --gpu-memory-utilization 0.90 \
            --dtype auto \
            2>&1 | tee logs/vllm_batch1_${sess}.log"
    echo "  [GPU $gpu] $model -> port $port (tmux: $sess, parser: $parser)"
done

echo ""
echo "Servers launching. Wait ~5-10 min for model loading."
echo "Check status:  bash scripts/launch_batch1_vllm.sh status"
echo "Stop all:      bash scripts/launch_batch1_vllm.sh stop"
