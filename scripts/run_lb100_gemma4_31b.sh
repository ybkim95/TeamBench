#!/usr/bin/env bash
# Launch gemma-4-31B-it 5-cond × 100-task ablation via local vLLM (0.19.0 in .venv).
set -o pipefail
cd /u/ybkim95/TeamBench

VENV=/u/ybkim95/TeamBench/.venv
HF_ID="google/gemma-4-31B-it"
SHORT="gemma4-31b"
PORT=8006
GPUS="2,3"
TP=2
OUTFILE="shared/ablation_results/lb100_${SHORT}_seed0.json"
LOG_SERVER="logs/vllm_${SHORT}_lb100.log"
LOG_EVAL="logs/eval_${SHORT}_lb100.log"

mkdir -p logs shared/ablation_results

echo "[$(date)] Starting vLLM server on GPUs $GPUS port $PORT TP=$TP" | tee -a "$LOG_EVAL"
CUDA_VISIBLE_DEVICES="$GPUS" "$VENV/bin/python" -u -m vllm.entrypoints.openai.api_server \
    --model "$HF_ID" \
    --port "$PORT" \
    --trust-remote-code \
    --enable-auto-tool-choice \
    --tool-call-parser gemma4 \
    --max-model-len 16384 \
    --gpu-memory-utilization 0.85 \
    --dtype bfloat16 \
    --tensor-parallel-size "$TP" \
    --enforce-eager > "$LOG_SERVER" 2>&1 &
SERVER_PID=$!
echo "[$(date)] Server PID=$SERVER_PID" | tee -a "$LOG_EVAL"

# Wait up to 40 min for server (large model + TP=2)
for i in $(seq 1 240); do
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
echo "[$(date)] FINISHED gemma-4-31B-it" | tee -a "$LOG_EVAL"
