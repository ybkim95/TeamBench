#!/usr/bin/env bash
# Launch gpt-oss-20b 5-cond × 100-task ablation via local vLLM (0.19.0 in .venv).
set -o pipefail
cd /u/ybkim95/TeamBench

VENV=/u/ybkim95/TeamBench/.venv
HF_ID="openai/gpt-oss-20b"
PORT=8005
GPUS="0"
OUTFILE="shared/ablation_results/lb100_gpt-oss-20b_seed0.json"
LOG_SERVER="logs/vllm_gpt-oss-20b_lb100.log"
LOG_EVAL="logs/eval_gpt-oss-20b_lb100.log"

mkdir -p logs shared/ablation_results

echo "[$(date)] Starting vLLM server on GPU $GPUS port $PORT" | tee -a "$LOG_EVAL"
CUDA_VISIBLE_DEVICES="$GPUS" "$VENV/bin/python" -u -m vllm.entrypoints.openai.api_server \
    --model "$HF_ID" \
    --port "$PORT" \
    --trust-remote-code \
    --enable-auto-tool-choice \
    --tool-call-parser openai \
    --max-model-len 32768 \
    --gpu-memory-utilization 0.85 \
    --dtype bfloat16 \
    --tensor-parallel-size 1 \
    --enforce-eager > "$LOG_SERVER" 2>&1 &
SERVER_PID=$!
echo "[$(date)] Server PID=$SERVER_PID" | tee -a "$LOG_EVAL"

# Wait up to 30 min for server
for i in $(seq 1 180); do
    if curl -s -m 2 "http://localhost:$PORT/v1/models" > /dev/null 2>&1; then
        echo "[$(date)] Server ready after $((i*10))s" | tee -a "$LOG_EVAL"
        break
    fi
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        echo "[$(date)] ERROR: server crashed. See $LOG_SERVER" | tee -a "$LOG_EVAL"
        tail -20 "$LOG_SERVER" | tee -a "$LOG_EVAL"
        exit 1
    fi
    sleep 10
done

if ! curl -s -m 3 "http://localhost:$PORT/v1/models" > /dev/null 2>&1; then
    echo "[$(date)] ERROR: server never started" | tee -a "$LOG_EVAL"
    kill $SERVER_PID 2>/dev/null; kill -9 $SERVER_PID 2>/dev/null
    exit 1
fi

echo "[$(date)] Running 5-cond × 100 ablation" | tee -a "$LOG_EVAL"
PYTHONUNBUFFERED=1 "$VENV/bin/python" -s scripts/run_leaderboard_100_ablation.py \
    --model "vllm:${HF_ID}@http://localhost:${PORT}/v1" \
    --seeds 0 \
    --output "$OUTFILE" 2>&1 | tee -a "$LOG_EVAL"

echo "[$(date)] Eval done, stopping server" | tee -a "$LOG_EVAL"
kill $SERVER_PID 2>/dev/null; sleep 3; kill -9 $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null
echo "[$(date)] FINISHED gpt-oss-20b" | tee -a "$LOG_EVAL"
