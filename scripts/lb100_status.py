#!/usr/bin/env python3
"""Unified LB100 evaluation status dashboard.

Shows all 100-task ablation evaluations in one place:
  - Completed models (final JSON files)
  - In-progress models (checkpoint files + process status)
  - Per-condition pass rates
"""
from __future__ import annotations

import json
import os
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path("/u/ybkim95/TeamBench/shared/ablation_results")
LOGS_DIR = Path("/u/ybkim95/TeamBench/logs")
LB_LOGS = Path("/u/ybkim95/TeamBench/shared/leaderboard/logs")

CONDITIONS = ["oracle", "restricted", "team_no_verify", "team_no_plan", "full"]
EXPECTED_PER_COND = 100  # 100 tasks per condition
EXPECTED_TOTAL = 500


def summarize_final(p: Path) -> dict:
    """Read a completed lb100 result file."""
    try:
        d = json.loads(p.read_text())
    except Exception as e:
        return {"error": str(e)}
    per = d.get("per_condition", {})
    return {
        "status": "COMPLETE",
        "per_condition": {c: per.get(c, {}).get("success_rate", 0.0) for c in CONDITIONS},
        "total_runs": sum(per.get(c, {}).get("total", 0) for c in CONDITIONS),
        "mtime": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
    }


def summarize_checkpoint(p: Path) -> dict:
    """Read a checkpoint (partial results).

    Dedupe by (condition, task_id, seed) keeping the LAST entry — handles
    regrade patches appended by regrade_lb100_checkpoint_safe.py.
    """
    try:
        lines = p.read_text().splitlines()
    except Exception as e:
        return {"error": str(e)}
    latest_by_key: dict[tuple, dict] = {}
    for line in lines:
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except Exception:
            continue
        key = (e.get("condition"), e.get("task_id"), e.get("seed"))
        latest_by_key[key] = e
    conds = defaultdict(int)
    passes_per_cond = defaultdict(int)
    for e in latest_by_key.values():
        c = e.get("condition", "?")
        conds[c] += 1
        if e.get("pass"):
            passes_per_cond[c] += 1
    return {
        "status": "IN-PROGRESS",
        "runs": sum(conds.values()),
        "conditions": dict(conds),
        "passes": dict(passes_per_cond),
        "mtime": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
    }


def running_processes() -> list[dict]:
    """Find all evaluation processes currently running."""
    out = subprocess.run(
        ["pgrep", "-af", "run_leaderboard_100_ablation|run_all_opensource_100_ablation"],
        capture_output=True, text=True
    )
    procs = []
    for line in out.stdout.strip().split("\n"):
        if not line or "pgrep" in line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) < 2:
            continue
        pid, cmd = parts
        procs.append({"pid": pid, "cmd": cmd[:120]})
    return procs


def extract_model_from_name(filename: str) -> str:
    """Extract model short name from lb100_<model>_seed0.json."""
    base = filename.replace("lb100_", "").replace("_seed0", "")
    base = base.replace(".json.checkpoint.jsonl", "").replace(".json", "")
    return base


def main() -> None:
    print("=" * 80)
    print(f"  LB100 STATUS DASHBOARD — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # 1. Running processes
    print("\n[RUNNING PROCESSES]")
    procs = running_processes()
    if not procs:
        print("  (none)")
    for p in procs:
        print(f"  pid={p['pid']:<8} {p['cmd']}")

    # 2. Scan all lb100 files in ROOT (exclude old_8192_results)
    final_files = sorted([p for p in ROOT.glob("lb100_*_seed0.json") if "oraclefull" not in p.name and p.name != "lb100_v1_seed0.json"])
    checkpoints = sorted([p for p in ROOT.glob("lb100_*_seed0.json.checkpoint.jsonl") if "oraclefull" not in p.name])

    final_models = {extract_model_from_name(p.name) for p in final_files}
    ckpt_models = {extract_model_from_name(p.name) for p in checkpoints}
    in_progress = ckpt_models - final_models

    # 3. Completed models
    print(f"\n[COMPLETED — {len(final_models)} models, 5-condition ablation]")
    print(f"  {'model':<25} {'total':>6}  {'oracle':>7} {'restr':>7} {'TnoV':>7} {'TnoP':>7} {'full':>7}  updated")
    for p in final_files:
        model = extract_model_from_name(p.name)
        s = summarize_final(p)
        if "error" in s:
            print(f"  {model:<25} ERROR: {s['error']}")
            continue
        pc = s["per_condition"]
        print(f"  {model:<25} {s['total_runs']:>6}  "
              f"{pc['oracle']:>6.1%} {pc['restricted']:>6.1%} "
              f"{pc['team_no_verify']:>6.1%} {pc['team_no_plan']:>6.1%} "
              f"{pc['full']:>6.1%}  {s['mtime']}")

    # 4. In-progress models
    print(f"\n[IN-PROGRESS — {len(in_progress)} models with checkpoints]")
    print(f"  {'model':<25} {'runs':>5}/{EXPECTED_TOTAL}  {'%':>5}  conditions                            updated")
    for p in checkpoints:
        model = extract_model_from_name(p.name)
        if model in final_models:
            continue  # already have final
        s = summarize_checkpoint(p)
        if "error" in s:
            print(f"  {model:<25} ERROR: {s['error']}")
            continue
        pct = s["runs"] * 100 // EXPECTED_TOTAL
        conds_str = " ".join(f"{c[:3]}={s['conditions'].get(c, 0)}" for c in CONDITIONS)
        print(f"  {model:<25} {s['runs']:>5}/{EXPECTED_TOTAL}  {pct:>4}%  {conds_str:<38}  {s['mtime']}")

    # 5. Old 8K results (for reference)
    old_dir = ROOT / "old_8192_results"
    old_files = sorted(old_dir.glob("lb100_*_seed0.json")) if old_dir.exists() else []
    if old_files:
        print(f"\n[OLD 8K RESULTS — {len(old_files)} models, not counted, kept for reference]")
        for p in old_files:
            model = extract_model_from_name(p.name)
            print(f"  {model}")

    # 6. Models queued in run script (not yet started)
    script = Path("/u/ybkim95/TeamBench/scripts/run_all_opensource_100_ablation.sh")
    if script.exists():
        queued = []
        for line in script.read_text().splitlines():
            line = line.strip()
            if line.startswith("run_model ") and not line.startswith("#"):
                # run_model "HF/ID" "short_name" ...
                parts = line.split('"')
                if len(parts) >= 4:
                    short = parts[3]
                    queued.append(short)
        not_started = [m for m in queued if m not in final_models and m not in in_progress]
        if not_started:
            print(f"\n[QUEUED — {len(not_started)} OSS models not yet started]")
            for m in not_started:
                print(f"  {m}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
