#!/usr/bin/env bash
set -euo pipefail
cd /u/ybkim95/TeamBench
export OPENAI_API_KEY="not-needed"

# Start vLLM
python3 -m vllm.entrypoints.openai.api_server \
  --model google/gemma-3-4b-it \
  --tensor-parallel-size 1 --port 8000 \
  --max-model-len 16384 --gpu-memory-utilization 0.85 \
  --enforce-eager --enable-auto-tool-choice --tool-call-parser hermes \
  > logs/vllm_4b_run.log 2>&1 &
VLLM_PID=$!

# Wait for ready
for i in $(seq 1 300); do
  curl -s http://localhost:8000/health >/dev/null 2>&1 && echo "[$(date)] vLLM ready after ${i}s" && break
  sleep 1
done

TASKS=$(python3 -c "import json; sel=json.load(open('../teambench.github.io/.omc/research/mini_v3_100tasks.json')); print(' '.join(sel['task_ids']))")

# Run eval with unbuffered output
python3 -u -m harness.batch_runner \
  --models "google/gemma-3-4b-it" \
  --tasks $TASKS \
  --seeds 0 \
  --tasks-dir tasks \
  --campaign-dir shared/gemma3_4b_campaign

echo "[$(date)] DONE"
kill $VLLM_PID 2>/dev/null
