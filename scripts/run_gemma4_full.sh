#!/usr/bin/env bash
set -euo pipefail

TEAMDIR="/u/ybkim95/TeamBench"
VENV="$TEAMDIR/venv_eval"
CAMPAIGN="shared/gemma4_campaign"
LOGDIR="$TEAMDIR/logs/gemma4_$(date +%Y%m%d_%H%M%S)"
USER_SP="/u/ybkim95/.local/lib/python3.10/site-packages"

mkdir -p "$TEAMDIR/$CAMPAIGN" "$LOGDIR"

# Fix path conflicts: temporarily hide user-site packages that clash with venv
HIDDEN_PKGS="transformers tokenizers huggingface_hub safetensors"
hide_user_pkgs() {
    for pkg in $HIDDEN_PKGS; do
        [ -d "$USER_SP/$pkg" ] && mv "$USER_SP/$pkg" "$USER_SP/_hidden_$pkg" 2>/dev/null || true
        for d in "$USER_SP"/${pkg}-*.dist-info; do
            [ -d "$d" ] && mv "$d" "${d}.hidden" 2>/dev/null || true
        done
    done
}
restore_user_pkgs() {
    for pkg in $HIDDEN_PKGS; do
        [ -d "$USER_SP/_hidden_$pkg" ] && mv "$USER_SP/_hidden_$pkg" "$USER_SP/$pkg" 2>/dev/null || true
        for d in "$USER_SP"/${pkg}-*.dist-info.hidden; do
            [ -d "$d" ] && mv "$d" "${d%.hidden}" 2>/dev/null || true
        done
    done
}
trap restore_user_pkgs EXIT

export OPENAI_API_KEY="not-needed"
export VLLM_BASE_URL="http://localhost:8000/v1"

TASKS=$($VENV/bin/python3 -c "import json; sel=json.load(open('$TEAMDIR/../teambench.github.io/.omc/research/mini_v3_100tasks.json')); print(' '.join(sel['task_ids']))")

cd "$TEAMDIR"

start_vllm() {
    local model=$1 tp=$2
    echo "[$(date)] Starting vLLM: $model (TP=$tp)"
    hide_user_pkgs
    $VENV/bin/python3 -m vllm.entrypoints.openai.api_server \
        --model "$model" --tensor-parallel-size "$tp" --port 8000 \
        --max-model-len 8192 --gpu-memory-utilization 0.90 \
        > "$LOGDIR/vllm_${model//\//_}.log" 2>&1 &
    VLLM_PID=$!
    for i in $(seq 1 600); do
        curl -s http://localhost:8000/health >/dev/null 2>&1 && echo "[$(date)] Ready after ${i}s" && return 0
        sleep 1
    done
    echo "[$(date)] FAILED to start"; kill $VLLM_PID 2>/dev/null; return 1
}

stop_vllm() {
    kill $VLLM_PID 2>/dev/null || true; wait $VLLM_PID 2>/dev/null || true
    sleep 3; fuser -k 8000/tcp 2>/dev/null || true; sleep 2
}

run_model() {
    local model=$1 tp=$2 short="${1//google\//}"
    echo ""; echo "=== $short (TP=$tp) — $(date) ==="
    start_vllm "$model" "$tp" || return 1
    $VENV/bin/python3 -m harness.batch_runner \
        --models "$model" --tasks $TASKS --seeds 0 \
        --tasks-dir tasks --resume "$CAMPAIGN" \
        2>&1 | tee "$LOGDIR/eval_${short}.log"
    stop_vllm
    echo "[$(date)] Done: $short"
}

echo "=== TeamBench × Gemma 4 — $(date) ==="
echo "Tasks: $(echo $TASKS | wc -w), Logs: $LOGDIR"

run_model "google/gemma-4-31B-it"      2 || echo "WARN: 31B failed"
run_model "google/gemma-4-26B-A4B-it"  1 || echo "WARN: 26B failed"
run_model "google/gemma-4-E4B-it"      1 || echo "WARN: E4B failed"
run_model "google/gemma-4-E2B-it"      1 || echo "WARN: E2B failed"

restore_user_pkgs
echo "=== ALL COMPLETE — $(date) ==="
