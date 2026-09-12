#!/usr/bin/env python3
"""Experiment X1: the compute-matched Solo-versus-Team budget response.

Why
---
Every published TeamBench comparison ran the conditions at different compute:
Solo 20 LLM turns, Restricted 30, two-role teams 40, Full Team up to 140. Any
Solo-versus-Team difference measured that way is confounded with a 7x budget gap.
harness/agent_loop.py::TurnBudget now gives every condition one shared allowance,
so the comparison can finally be made at equal compute.

This runs both Solo and Full Team across a ladder of identical total budgets and
produces the budget-response curve for each. The decisive question the paper asks
is not "does the team beat Solo" but "at equal compute, does it".

Design
------
  tasks       25-task stratified subset (experiments/role_enforcement_ablation/
              config/task_selection.json::selected_flat)
  conditions  ORACLE (Solo, full spec) and FULL (Planner+Executor+Verifier)
  budgets     total_turns in {20, 60, 140}, identical for both conditions
  seed        0
  runs        25 tasks x 2 conditions x 3 budgets = 150

Caveat recorded for the paper: the 25-task subset was stratified on the TNI
classification in shared/paper/tni_report.json, and TNI has since been shown to
be an unreliable per-task statistic (single-run reliability 0.06). The subset is
therefore a stratified sample on a noisy variable, which is fine for a paired
within-task comparison but must not be read as difficulty-balanced.

Usage:
  python scripts/run_budget_sweep.py --model gemini-3-flash-preview
  python scripts/run_budget_sweep.py --model gemini-3-flash-preview --budgets 20 60 --limit 5
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

SELECTION = os.path.join(
    REPO, "experiments/role_enforcement_ablation/config/task_selection.json")
OUT_DIR = os.path.join(REPO, "shared", "ablation_results", "budget_sweep")


def load_tasks(selection_path: str | None = None) -> list[str]:
    """Task ids for the sweep.

    Defaults to the original 25-task role-enforcement subset. That subset is a
    poor fit for discriminative rescoring: 24 of its 25 graders hand-roll
    score.json instead of using harness/grader_helpers.sh, so they emit no
    per-check results and their runs can only ever be read on the old scale,
    where the do-nothing floor is ~0.58. Pass --tasks-file to run the sweep on a
    selection whose graders do emit checklists.
    """
    src = selection_path or SELECTION
    raw = json.load(open(src))
    sel = raw["selected_flat"] if isinstance(raw, dict) else raw
    # config stores lowercase ids; the task dirs are mixed case
    on_disk = {d.lower(): d for d in os.listdir(os.path.join(REPO, "tasks"))}
    out = []
    for t in sel:
        real = on_disk.get(t.lower())
        if real:
            out.append(real)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemini-3-flash-preview")
    ap.add_argument("--budgets", nargs="+", type=int, default=[20, 60, 140])
    ap.add_argument("--seeds", nargs="+", type=int, default=[0])
    ap.add_argument("--tasks-file", default=None,

                    help="JSON list of task ids, or an object with "

                         "selected_flat. Defaults to the original subset.")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()

    from harness.ablation import AblationCondition, run_full_ablation

    tasks = load_tasks(a.tasks_file)
    if a.limit:
        tasks = tasks[: a.limit]
    # A sweep on a different task selection must not collide with an earlier
    # one: same budget, same model, different tasks. Namespace the output by
    # the selection so results are never silently reused across selections.
    out_dir = OUT_DIR
    if a.tasks_file:
        tag_sel = os.path.splitext(os.path.basename(a.tasks_file))[0]
        out_dir = os.path.join(OUT_DIR, tag_sel)
    os.makedirs(out_dir, exist_ok=True)

    conds = [AblationCondition.ORACLE, AblationCondition.FULL]
    total = len(tasks) * len(conds) * len(a.budgets) * len(a.seeds)
    print(f"[sweep] model={a.model} tasks={len(tasks)} budgets={a.budgets} "
          f"seeds={a.seeds} -> {total} runs", flush=True)

    tag = a.model.replace("/", "_").replace("-", "").replace(".", "")
    for b in a.budgets:
        out = os.path.join(out_dir, f"budget{b}_{tag}.json")
        if os.path.isfile(out):
            print(f"[sweep] budget={b} already done, skipping ({out})", flush=True)
            continue
        print(f"\n[sweep] ===== total_turns={b} =====", flush=True)
        t0 = time.time()
        run_full_ablation(
            model=a.model, tasks=tasks, seeds=a.seeds,
            tasks_dir=os.path.join(REPO, "tasks"), output=out,
            max_turns=b, max_remediation=2, conditions=conds,
            total_turns=b,
        )
        print(f"[sweep] budget={b} done in {time.time()-t0:.0f}s -> {out}", flush=True)

    print("\n[sweep] all budgets complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
