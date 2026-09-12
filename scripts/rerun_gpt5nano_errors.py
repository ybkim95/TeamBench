#!/usr/bin/env python3
"""Re-run the 9 errored gpt-5-nano tasks and update the results file."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.ablation import run_full_ablation, AblationCondition

RESULTS_FILE = "shared/ablation_results/lb100_gpt5nano_oraclefull_seed0.json"
CHECKPOINT_FILE = RESULTS_FILE + ".checkpoint.jsonl"

# Load current results and find errored tasks
with open(RESULTS_FILE) as f:
    data = json.load(f)

errored = [(r["condition"], r["task_id"]) for r in data["runs"] if r.get("error")]
print(f"Found {len(errored)} errored runs to re-run:")
for cond, tid in errored:
    print(f"  {cond} x {tid}")

# Remove errored entries from checkpoint so they get re-run
entries = [json.loads(l) for l in open(CHECKPOINT_FILE)]
clean = [e for e in entries if not e.get("error")]
with open(CHECKPOINT_FILE, "w") as f:
    for e in clean:
        f.write(json.dumps(e) + "\n")
print(f"\nCleaned checkpoint: {len(entries)} -> {len(clean)} entries")

# Remove the completed output file so it gets regenerated
os.rename(RESULTS_FILE, RESULTS_FILE + ".pre_rerun_backup")
print(f"Backed up old results")

# Re-run full ablation (will skip checkpointed tasks, only run missing ones)
# Get unique task list from errored entries
all_tasks = []
seen = set()
for r in data["runs"]:
    if r["task_id"] not in seen:
        seen.add(r["task_id"])
        all_tasks.append(r["task_id"])

print(f"\nRunning ablation on {len(all_tasks)} tasks (will skip {len(clean)} checkpointed)...")
run_full_ablation(
    model="gpt-5-nano",
    tasks=all_tasks,
    seeds=[0],
    tasks_dir="tasks",
    output=RESULTS_FILE,
    conditions=[AblationCondition.ORACLE, AblationCondition.FULL],
)
print(f"\nDone! Results saved to {RESULTS_FILE}")
