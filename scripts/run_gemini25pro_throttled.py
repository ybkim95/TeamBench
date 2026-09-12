#!/usr/bin/env python3
"""Run gemini-2.5-pro with throttling between runs to avoid rate limits.

Wraps run_full_ablation with a monkey-patched sleep between runs.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.ablation import run_full_ablation, AblationCondition

# Load 100-task set
TASKS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "leaderboard", "data", "leaderboard_100_tasks.json",
)
with open(TASKS_FILE) as f:
    _data = json.load(f)
    _seen = set()
    TASKS = []
    for t in _data["tasks"]:
        if t["task_id"] not in _seen:
            _seen.add(t["task_id"])
            TASKS.append(t["task_id"])

# Monkey-patch the retry function to add inter-run delay
import harness.gemini_adapter as gmod

_original_call = gmod.GeminiAdapter._call_with_retry.__wrapped__ if hasattr(gmod.GeminiAdapter._call_with_retry, '__wrapped__') else None

# Add delay between runs via a wrapper around run_ablation_condition
import harness.ablation as amod
_orig_run_condition = amod.run_ablation_condition

_run_count = 0
def _throttled_run_condition(*args, **kwargs):
    global _run_count
    _run_count += 1
    if _run_count > 1:
        delay = 30  # 30s delay between runs
        print(f"  [throttle] Waiting {delay}s before next run...")
        time.sleep(delay)
    return _orig_run_condition(*args, **kwargs)

amod.run_ablation_condition = _throttled_run_condition

CONDITIONS = [AblationCondition.ORACLE, AblationCondition.FULL]

outpath = "shared/ablation_results/lb100_gemini25pro_oraclefull_seed0.json"

print(f"TeamBench 100-Task Leaderboard Ablation (THROTTLED)")
print(f"=" * 60)
print(f"  Model:      gemini-2.5-pro-preview-05-06")
print(f"  Tasks:      {len(TASKS)}")
print(f"  Seeds:      [0]")
print(f"  Conditions: {[c.value for c in CONDITIONS]}")
print(f"  Output:     {outpath}")
print(f"  Throttle:   30s between runs")
print(f"=" * 60)

run_full_ablation(
    model="gemini-2.5-pro-preview-05-06",
    tasks=TASKS,
    seeds=[0],
    tasks_dir="tasks",
    output=outpath,
    conditions=CONDITIONS,
)

print(f"\nResults saved to {outpath}")
