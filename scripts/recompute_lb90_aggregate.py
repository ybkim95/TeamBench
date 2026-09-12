#!/usr/bin/env python3
"""Restrict the LB100 per-model 5-condition aggregate to the LB90 task set.

Reads `shared/ablation_results/lb100_*.{json,jsonl}`, drops every record
whose task_id is in the LB90 dropped list, and produces a per-model
per-condition `passed / valid_n / rate` table that is directly substitutable
for `shared/paper/lb100_full_aggregate.json` (same shape).

Output:
  shared/paper/lb90_full_aggregate.json
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ABL = os.path.join(REPO, "shared/ablation_results")
OUT = os.path.join(REPO, "shared/paper/lb90_full_aggregate.json")
LB90_PATH = os.path.join(REPO, "leaderboard/data/leaderboard_90_tasks.json")

CONDITIONS = ("oracle", "restricted", "team_no_plan", "team_no_verify", "full")


def model_from_filename(fn: str) -> str:
    n = fn[len("lb100_"):]
    for suf in (".json", ".checkpoint.jsonl"):
        if n.endswith(suf):
            n = n[: -len(suf)]
    for tag in ("_oraclefull_seed0", "_3cond_seed0", "_5cond_seed0", "_seed0",
                "_full_resume", "_REVERSE", "_FWD", "_REV"):
        if n.endswith(tag):
            n = n[: -len(tag)]
    # Map raw model slug to "human" model name used in lb100_full_aggregate.json
    return n


# Map filename slugs to canonical model keys (matches lb100_full_aggregate.json)
SLUG_TO_KEY = {
    "haiku45": "claude-haiku-4-5",
    "sonnet46": "claude-sonnet-4-6",
    "opus47": "claude-opus-4-7",
    "gpt54": "gpt-5-4",
    "gpt5mini": "gpt-5-4-mini",
    "gpt-5.4-mini": "gpt-5-4-mini",
    "gpt5nano": "gpt-5-nano",
    "gpt-5.4-nano": "gpt-5-4-nano",
    "g3flash": "gemini-3-flash-preview",
    "gemini3flash": "gemini-3-flash-preview",
    "g31lite": "gemini-3-1-flash-lite-preview",
    "gemini31lite": "gemini-3-1-flash-lite-preview",
    "gemini-3.1-pro-preview": "gemini-3-1-pro-preview",
    "gemini25pro": "gemini-2-5-pro",
    "gemma4-31b": "gemma-4-31b",
    "qwen3-8b-or": "qwen3-8b",
    "qwen3-14b-or": "qwen3-14b",
    "qwen3-32b-or": "qwen3-32b",
    "qwen3-30b-a3b-or": "qwen3-30b-a3b",
    "qwen3-4b": "qwen3-4b",
    "qwen3-8b": "qwen3-8b",
    "qwen35-0.8b": "qwen3.5-0.8b",
    "gpt-oss-20b": "gpt-oss-20b",
    "gpt-oss-120b": "gpt-oss-120b",
}


def normalize_model_key(slug: str) -> str:
    return SLUG_TO_KEY.get(slug, slug)


def main():
    lb90 = json.load(open(LB90_PATH))
    lb90_ids = {t["task_id"] if isinstance(t, dict) else t for t in lb90["tasks"]}
    dropped = set(lb90.get("dropped_task_ids", []))
    print(f"[lb90] LB90 task set: {len(lb90_ids)}  (dropping {len(dropped)} from LB100)")

    # model -> condition -> {passed, valid_n, source(s)}
    by_model_cond = defaultdict(lambda: defaultdict(lambda: {"passed": 0, "valid_n": 0, "sources": set()}))

    for fn in sorted(os.listdir(ABL)):
        if not fn.startswith("lb100_") or any(s in fn for s in ("invalid", "archived", "pre_", ".bak")):
            continue
        path = os.path.join(ABL, fn)
        if not os.path.isfile(path):
            continue
        slug = model_from_filename(fn)
        records = []
        if fn.endswith(".json"):
            try:
                d = json.load(open(path))
            except Exception:
                continue
            records = d.get("runs", []) if isinstance(d, dict) else (d if isinstance(d, list) else [])
        elif fn.endswith(".checkpoint.jsonl"):
            for line in open(path):
                try:
                    records.append(json.loads(line))
                except Exception:
                    continue

        for r in records:
            if not isinstance(r, dict):
                continue
            tid = r.get("task_id") or r.get("task")
            if not tid or tid not in lb90_ids:
                continue
            cond = r.get("condition")
            if cond not in CONDITIONS:
                continue
            mk = normalize_model_key(slug)
            cell = by_model_cond[mk][cond]
            # Treat errored runs as excluded (consistent with original aggregate)
            err = r.get("error")
            if err:
                continue
            cell["valid_n"] += 1
            if r.get("pass") or r.get("passed"):
                cell["passed"] += 1
            cell["sources"].add(fn)

    # Build output in same shape as lb100_full_aggregate.json
    models = {}
    for mk, cm in by_model_cond.items():
        models[mk] = {}
        for cond in CONDITIONS:
            cell = cm.get(cond, {})
            n = cell.get("valid_n", 0)
            p = cell.get("passed", 0)
            srcs = sorted(cell.get("sources", set()))
            if n > 0:
                models[mk][cond] = {
                    "passed": p,
                    "valid_n": n,
                    "rate": round(p / n, 4),
                    "source": "+".join(srcs[:3]) + (f" (+{len(srcs)-3} more)" if len(srcs) > 3 else ""),
                }
            else:
                models[mk][cond] = {"passed": 0, "valid_n": 0, "rate": None, "source": None}

    payload = {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "parent": "lb100_full_aggregate.json",
        "task_set": "leaderboard_90_tasks.json (TeamBench-90)",
        "n_tasks": len(lb90_ids),
        "dropped_from_lb100": sorted(dropped),
        "models": models,
    }
    json.dump(payload, open(OUT, "w"), indent=2)
    print(f"[lb90] wrote {OUT}")
    print(f"[lb90] {len(models)} model rows")

    # Print sorted-by-Full table for sanity
    def srt(k):
        f = models[k].get("full") or {}
        return -(f.get("rate") if f.get("rate") is not None else -1)

    print()
    print(f'{"model":<30} | {"oracle":>14} | {"restrict":>14} | {"no_plan":>14} | {"no_verify":>14} | {"full":>14}')
    for k in sorted(models, key=srt):
        row = models[k]; parts = [k[:30].ljust(30)]
        for c in CONDITIONS:
            cell = row.get(c) or {}
            r = cell.get("rate"); n = cell.get("valid_n", 0); ps = cell.get("passed", 0)
            if r is None or n == 0:
                parts.append("TBA".rjust(14))
            else:
                parts.append(f"{ps}/{n}={100*r:.1f}%".rjust(14))
        print(" | ".join(parts))


if __name__ == "__main__":
    main()
