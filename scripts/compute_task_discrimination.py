#!/usr/bin/env python3
"""Compute per-task model-discrimination scores from existing LB100 ablation runs.

For each LB100 task, harvest pass/fail records across all (model, condition)
cells from `shared/ablation_results/lb100_*.{json,checkpoint.jsonl}`.  For
each condition compute:

    discrimination[task, condition] = max(model_pass_rate) - min(model_pass_rate)

Then aggregate per-task:

    discrimination_score = max over conditions of the per-condition spread

Tasks with `discrimination_score < 0.1` are flagged: every model gets the
same outcome, which means the task is either trivial (everyone passes) or
broken (everyone fails) — informative either way.

Output:
  - `shared/paper/teambench_quality/task_discrimination.json` (per-task)
  - Adds `discrimination_score` and `discrimination_per_condition` to each
    `shared/validation_reports/<task>.json` (where one exists).

Usage:
    python scripts/compute_task_discrimination.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LB100_PATH = os.path.join(REPO, "leaderboard/data/leaderboard_100_tasks.json")
ABL_DIR = os.path.join(REPO, "shared/ablation_results")
OUT = os.path.join(REPO, "shared/paper/teambench_quality/task_discrimination.json")
VAL_REPORTS_DIR = os.path.join(REPO, "shared/validation_reports")
os.makedirs(os.path.dirname(OUT), exist_ok=True)


def model_from_filename(fn: str) -> str:
    """Extract a canonical model slug from an lb100_*.{json,jsonl} filename."""
    n = fn[len("lb100_"):]
    for suf in (".json", ".checkpoint.jsonl"):
        if n.endswith(suf):
            n = n[: -len(suf)]
    for tag in ("_oraclefull_seed0", "_3cond_seed0", "_5cond_seed0", "_seed0",
                "_full_resume", "_REVERSE", "_FWD", "_REV"):
        if n.endswith(tag):
            n = n[: -len(tag)]
    return n


def harvest():
    by_task_cond_model = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0, 0])))
    # by_task_cond_model[task][condition][model] = [n_total, n_pass]
    if not os.path.isdir(ABL_DIR):
        return by_task_cond_model
    for fn in sorted(os.listdir(ABL_DIR)):
        if not fn.startswith("lb100_"):
            continue
        if any(s in fn for s in ("invalid", "archived", "pre_", ".bak")):
            continue
        path = os.path.join(ABL_DIR, fn)
        if not os.path.isfile(path):
            continue
        # Default model slug = filename slug; will be overridden by file-level model field if present
        file_model = model_from_filename(fn)
        records = []
        file_level_model = None
        if fn.endswith(".json"):
            try:
                d = json.load(open(path))
            except Exception:
                continue
            if isinstance(d, dict):
                file_level_model = d.get("model") or d.get("backend") or None
                if "runs" in d and isinstance(d["runs"], list):
                    records = d["runs"]
                else:
                    continue
            elif isinstance(d, list):
                records = d
            else:
                continue
        elif fn.endswith(".checkpoint.jsonl"):
            for line in open(path):
                try:
                    records.append(json.loads(line))
                except Exception:
                    continue
            # Checkpoint files don't have file-level model header; rely on filename slug
        # Use file-level model if present, else fallback to filename slug
        model = file_level_model or file_model
        for r in records:
            if not isinstance(r, dict):
                continue
            tid = r.get("task_id") or r.get("task")
            cond = r.get("condition")
            if not tid or not cond:
                continue
            # Per-record model override (rare, but some files mix models)
            row_model = r.get("model") or model
            cell = by_task_cond_model[tid][cond][row_model]
            cell[0] += 1
            if r.get("pass") or r.get("passed"):
                cell[1] += 1
    return by_task_cond_model


def compute(by_task_cond_model):
    out = {}
    for tid, cond_map in by_task_cond_model.items():
        per_cond = {}
        for cond, model_map in cond_map.items():
            # LB100 is seed 0 only, so n per (task, model, cond) is typically 1.
            # We require n >= 1 and at least 2 distinct models.
            rates = []
            for model, (n, p) in model_map.items():
                if n >= 1:
                    rates.append((model, p / n, n))
            if len(rates) >= 2:
                rs = [r for _, r, _ in rates]
                spread = round(max(rs) - min(rs), 4)
                per_cond[cond] = {
                    "spread": spread,
                    "n_models": len(rates),
                    "min_rate": round(min(rs), 4),
                    "max_rate": round(max(rs), 4),
                    "rates_by_model": {m: round(r, 4) for m, r, _ in rates},
                }
        if per_cond:
            score = round(max(c["spread"] for c in per_cond.values()), 4)
            out[tid] = {
                "discrimination_score": score,
                "per_condition": {k: {kk: vv for kk, vv in v.items() if kk != "rates_by_model"} for k, v in per_cond.items()},
                "best_condition": max(per_cond, key=lambda k: per_cond[k]["spread"]),
                "rates_by_model_per_condition": {k: v["rates_by_model"] for k, v in per_cond.items()},
            }
    return out


def main():
    print(f"[discrim] harvesting from {ABL_DIR}")
    by = harvest()
    print(f"[discrim] tasks observed in run records: {len(by)}")
    out = compute(by)

    # Restrict reporting to LB100 ids
    lb100 = json.load(open(LB100_PATH))["tasks"]
    lb100_ids = [t["task_id"] if isinstance(t, dict) else t for t in lb100]
    lb100_only = {tid: out[tid] for tid in lb100_ids if tid in out}
    missing = [tid for tid in lb100_ids if tid not in out]

    payload = {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "n_lb100_with_data": len(lb100_only),
        "n_lb100_missing_data": len(missing),
        "missing": missing,
        "summary": {
            "discrim_lt_0.05": sum(1 for v in lb100_only.values() if v["discrimination_score"] < 0.05),
            "discrim_lt_0.10": sum(1 for v in lb100_only.values() if v["discrimination_score"] < 0.10),
            "discrim_ge_0.20": sum(1 for v in lb100_only.values() if v["discrimination_score"] >= 0.20),
            "discrim_ge_0.40": sum(1 for v in lb100_only.values() if v["discrimination_score"] >= 0.40),
        },
        "tasks": lb100_only,
    }
    json.dump(payload, open(OUT, "w"), indent=2)
    print(f"[discrim] wrote {OUT}")
    print(f"[discrim] summary: {payload['summary']}")
    print(f"[discrim] LB100 missing run-record data for {len(missing)} tasks")

    # Append discrimination_score into existing validation reports
    appended = 0
    for tid, info in lb100_only.items():
        rep_path = os.path.join(VAL_REPORTS_DIR, f"{tid}.json")
        if not os.path.isfile(rep_path):
            continue
        try:
            rep = json.load(open(rep_path))
        except Exception:
            continue
        rep.setdefault("supplementary", {})["discrimination_score"] = info["discrimination_score"]
        rep["supplementary"]["discrimination_per_condition"] = info["per_condition"]
        json.dump(rep, open(rep_path, "w"), indent=2)
        appended += 1
    print(f"[discrim] appended discrimination_score into {appended} validation reports")


if __name__ == "__main__":
    main()
