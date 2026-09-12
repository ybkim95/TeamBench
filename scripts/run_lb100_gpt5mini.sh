#!/usr/bin/env bash
# Run lb100 5-condition ablation on GPT-5.4-mini (500 runs total).
set -euo pipefail
cd "$(dirname "$0")/.."

PY=/u/ybkim95/TeamBench/venv/bin/python
TASKS=$("$PY" -c "import json; d=json.load(open('leaderboard/data/leaderboard_100_tasks.json')); print(' '.join(t['task_id'] for t in d['tasks']))")

OUT=shared/ablation_results/lb100_gpt5mini_5cond_seed0.json

"$PY" -u -m harness.ablation \
    --model gpt-5.4-mini \
    --tasks $TASKS \
    --seeds 0 \
    --conditions oracle restricted team_no_plan team_no_verify full \
    --output "$OUT" \
    --max-turns 20
