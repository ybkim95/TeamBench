#!/usr/bin/env python3
"""Who talks to whom in a Planner/Executor/Verifier run, counted from the logs.

Why this exists
---------------
The paper claims the coordination channel is nominally bidirectional and
empirically one-directional, and cites a message count for it. That number was
first produced ad hoc, which makes the paper's most mechanistic claim the least
reproducible thing in it. scripts/communication_analysis.py does not answer it:
it aggregates every historical team run, while the claim is about the runs in
the compute-matched core sweep.

This reads messages/dialogue.jsonl under the run directories named by a sweep's
own checkpoints, so the population is exactly the runs the claim is about.

Usage:
  python scripts/message_flow.py \
    --dir shared/ablation_results/budget_sweep/core_tasks \
    --model gemini3flashpreview --out shared/paper/quality/message_flow.json
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def dialogue(run_dir: str) -> list:
    p = os.path.join(run_dir, "messages", "dialogue.jsonl")
    if not os.path.isfile(p):
        return []
    out = []
    for line in open(p):
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(
        REPO, "shared/ablation_results/budget_sweep/core_tasks"))
    ap.add_argument("--model", default="gemini3flashpreview")
    ap.add_argument("--condition", default="full")
    ap.add_argument("--out", default=os.path.join(
        REPO, "shared/paper/quality/message_flow.json"))
    a = ap.parse_args()

    runs, missing, budgets = [], 0, set()
    for cp in sorted(glob.glob(os.path.join(a.dir, "*%s*.checkpoint.jsonl" % a.model))):
        b = int(re.search(r"budget(\d+)_", os.path.basename(cp)).group(1))
        for line in open(cp):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("condition") != a.condition:
                continue
            # A run that died on infrastructure sent no messages; counting it
            # would deflate the per-run averages with a structural zero.
            if r.get("error"):
                continue
            rd = r.get("run_dir") or ""
            if not os.path.isdir(rd):
                missing += 1
                continue
            budgets.add(b)
            runs.append((b, r.get("task_id"), dialogue(rd)))

    if not runs:
        print("no run directories found under %s" % a.dir, file=sys.stderr)
        return 1

    pair = collections.Counter()
    per_run_total, back_channel_runs = [], 0
    uniq = []
    for _b, _t, msgs in runs:
        n = 0
        seen = collections.defaultdict(list)
        for m in msgs:
            if m.get("type") != "message":
                continue
            src, dst = (m.get("role") or "?"), (m.get("to") or "?")
            pair[(src, dst)] += 1
            seen[(src, dst)].append((m.get("content") or "").strip())
            n += 1
        per_run_total.append(n)
        if pair and seen.get(("executor", "planner")):
            back_channel_runs += 1
        for k, v in seen.items():
            if k == ("planner", "executor") and v:
                uniq.append(len(set(v)) / len(v))

    total = sum(pair.values())
    pe = pair.get(("planner", "executor"), 0)
    ep = pair.get(("executor", "planner"), 0)
    res = {
        "model": a.model, "condition": a.condition,
        "budgets": sorted(budgets), "runs": len(runs),
        "run_dirs_missing": missing,
        "messages_total": total,
        "by_pair": {"%s->%s" % k: v for k, v in sorted(
            pair.items(), key=lambda kv: -kv[1])},
        "planner_to_executor": pe,
        "planner_to_executor_share": (pe / total) if total else None,
        "executor_to_planner": ep,
        "runs_with_any_back_channel": back_channel_runs,
        "messages_per_run_mean": statistics.mean(per_run_total) if per_run_total else None,
        "planner_msg_distinct_fraction_median": (
            statistics.median(uniq) if uniq else None),
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)

    print("runs %d over budgets %s (%d run dirs missing)"
          % (res["runs"], res["budgets"], missing))
    print("messages %d total, %.1f per run" % (total, res["messages_per_run_mean"]))
    for k, v in res["by_pair"].items():
        print("  %-24s %6d  %5.1f%%" % (k, v, 100 * v / total))
    print("planner->executor %.1f%%   executor->planner %d message(s) "
          "across %d runs" % (100 * res["planner_to_executor_share"], ep, len(runs)))
    print("median distinct fraction of planner messages within a run: %s"
          % res["planner_msg_distinct_fraction_median"])
    print("wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
