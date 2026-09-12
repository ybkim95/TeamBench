#!/usr/bin/env bash
# Launch all 3 Qwen3 vLLM servers in background tmux sessions.
#
# Usage: bash scripts/launch_all_vllm.sh
#
# GPU allocation:
#   GPU 1 -> Qwen3-4B  (port 8001, ~8GB)
#   GPU 2 -> Qwen3-8B  (port 8002, ~16GB)
#   GPU 3 -> Qwen3-14B (port 8003, ~28GB)
#
# GPU 0 is left free (partially in use).
# Monitor: tmux attach -t vllm-4b / vllm-8b / vllm-14b
# Stop all: bash scripts/launch_all_vllm.sh stop

set -euo pipefail
cd "$(dirname "$0")/.."

if [ "${1:-}" = "stop" ]; then
    echo "Stopping all vLLM servers..."
    tmux kill-session -t vllm-4b  2>/dev/null && echo "  Stopped vllm-4b"  || echo "  vllm-4b not running"
    tmux kill-session -t vllm-8b  2>/dev/null && echo "  Stopped vllm-8b"  || echo "  vllm-8b not running"
    tmux kill-session -t vllm-14b 2>/dev/null && echo "  Stopped vllm-14b" || echo "  vllm-14b not running"
    exit 0
fi

echo "Launching Qwen3 vLLM servers..."
echo ""

# Qwen3-4B on GPU 1
tmux kill-session -t vllm-4b 2>/dev/null || true
tmux new-session -d -s vllm-4b "bash scripts/serve_vllm.sh Qwen/Qwen3-4B 1 8001"
echo "  [GPU 1] Qwen3-4B  -> port 8001 (tmux: vllm-4b)"

# Qwen3-8B on GPU 2
tmux kill-session -t vllm-8b 2>/dev/null || true
tmux new-session -d -s vllm-8b "bash scripts/serve_vllm.sh Qwen/Qwen3-8B 2 8002"
echo "  [GPU 2] Qwen3-8B  -> port 8002 (tmux: vllm-8b)"

# Qwen3-14B on GPU 3
tmux kill-session -t vllm-14b 2>/dev/null || true
tmux new-session -d -s vllm-14b "bash scripts/serve_vllm.sh Qwen/Qwen3-14B 3 8003"
echo "  [GPU 3] Qwen3-14B -> port 8003 (tmux: vllm-14b)"

echo ""
echo "Servers launching in background. Wait ~2-5 min for model loading."
echo "Check status:  python scripts/run_qwen_experiments.py --model all --check-only"
echo "View logs:     tmux attach -t vllm-8b"
echo "Stop all:      bash scripts/launch_all_vllm.sh stop"
