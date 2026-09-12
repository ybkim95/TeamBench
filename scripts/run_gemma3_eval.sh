#!/usr/bin/env bash
# TeamBench × Gemma 3 Evaluation — 100 tasks, all ablation conditions
set -euo pipefail

TEAMDIR="/u/ybkim95/TeamBench"
CAMPAIGN="shared/gemma3_campaign"
LOGDIR="$TEAMDIR/logs/gemma3_$(date +%Y%m%d_%H%M%S)"

mkdir -p "$TEAMDIR/$CAMPAIGN" "$LOGDIR"

export OPENAI_API_KEY="not-needed"
export VLLM_BASE_URL="http://localhost:8000/v1"

TASKS=$(python3 -c "import json; sel=json.load(open('$TEAMDIR/../teambench.github.io/.omc/research/mini_v3_100tasks.json')); print(' '.join(sel['task_ids']))")

cd "$TEAMDIR"

start_vllm() {
    local model=$1 tp=$2
    echo "[$(date)] Starting vLLM: $model (TP=$tp)"
    python3 -m vllm.entrypoints.openai.api_server \
        --model "$model" --tensor-parallel-size "$tp" --port 8000 \
        --max-model-len 4096 --gpu-memory-utilization 0.90 \
        > "$LOGDIR/vllm_${model//\//_}.log" 2>&1 &
    VLLM_PID=$!
    for i in $(seq 1 600); do
        curl -s http://localhost:8000/health >/dev/null 2>&1 && echo "[$(date)] Ready after ${i}s" && return 0
        sleep 1
    done
    echo "[$(date)] FAILED"; kill $VLLM_PID 2>/dev/null; return 1
}

stop_vllm() {
    kill $VLLM_PID 2>/dev/null || true; wait $VLLM_PID 2>/dev/null || true
    sleep 3; fuser -k 8000/tcp 2>/dev/null || true; sleep 2
}

run_model() {
    local model=$1 tp=$2 short="${1//google\//}"
    echo ""; echo "=== $short (TP=$tp) — $(date) ==="
    start_vllm "$model" "$tp" || return 1
    python3 -m harness.batch_runner \
        --models "$model" --tasks $TASKS --seeds 0 \
        --tasks-dir tasks --resume "$CAMPAIGN" \
        2>&1 | tee "$LOGDIR/eval_${short}.log"
    stop_vllm
    echo "[$(date)] Done: $short"
}

echo "=== TeamBench × Gemma 3 — $(date) ==="
echo "Tasks: $(echo $TASKS | wc -w), Logs: $LOGDIR"

run_model "google/gemma-3-27b-it" 4 || echo "WARN: 27b failed"
run_model "google/gemma-3-4b-it"  1 || echo "WARN: 4b failed"

echo "=== ALL COMPLETE — $(date) ==="
