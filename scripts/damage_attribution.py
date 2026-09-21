#!/usr/bin/env python3
"""Which role damages the workspace, measured rather than asserted.

Why
---
The paper explained a real measurement, that team runs trip the guard checks
more often than solo runs, with an unmeasured story: "three roles means three
hands editing a repository without seeing what the others did." The premise is
false. Of the three roles only two can touch the workspace at all:

  planner   ReadFileTool over the spec and message directories, SendMessageTool.
            No workspace tool of any kind, and the prompt says so.
  executor  RunCommandTool with cwd=workspace and WriteFileTool over it.
  verifier  WriteFileTool restricted to the submission directory, but
            RunCommandTool with cwd=workspace, so a shell command reaches the
            workspace even though the write tool does not.

So the question is not rhetorical, it is answerable: every tool call is logged
per role and per phase, so the destructive ones can be attributed.

This reads logs/<role>/[phase/]turn_*.json under the run directories a sweep's
checkpoints name, and counts commands that can destroy work. It reports what it
finds, including the case where the story the paper told is simply not there.

Usage:
  python scripts/damage_attribution.py --model gemini3flashpreview
"""
from __future__ import annotations

import argparse
import collections
import glob
import importlib.util
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Commands that mutate existing files in place. Read this as "workspace-mutating",
# NOT as "damaging": sed -i and shell redirection are how an agent edits, and they
# dominate the counts. An agent that edits more trips this more, so the per-run
# totals compare editing volume and must not be read as a damage rate. What the
# list supports is attribution: given a run that a guard check says was damaged,
# which role issued mutating commands in it.
DESTRUCTIVE = [
    ("rm", r"\brm\s+(-\w+\s+)*"),
    ("git checkout/restore", r"\bgit\s+(checkout|restore)\b"),
    ("git clean", r"\bgit\s+clean\b"),
    ("git reset --hard", r"\bgit\s+reset\s+--hard\b"),
    ("truncate/overwrite", r"(^|\s|;|&&|\|)>\s*\S|\btruncate\b|\b:\s*>\s*\S"),
    ("mv over existing", r"\bmv\s+"),
    ("sed -i", r"\bsed\s+-i\b"),
    ("find -delete", r"\bfind\b.*-delete\b"),
]


def phase_of(path: str, role: str) -> str:
    """The phase a turn log belongs to, from its directory under logs/<role>/."""
    rel = path.split(os.sep + "logs" + os.sep, 1)[-1]
    parts = rel.split(os.sep)
    return parts[1] if len(parts) > 2 else "main"


def scan_run(run_dir: str) -> list:
    out = []
    logs = os.path.join(run_dir, "logs")
    if not os.path.isdir(logs):
        return out
    for path in glob.glob(os.path.join(logs, "*", "**", "turn_*.json"),
                          recursive=True):
        role = os.path.relpath(path, logs).split(os.sep)[0]
        try:
            d = json.load(open(path))
        except Exception:
            continue
        for call in (d.get("tool_calls") or []):
            args = call.get("args") or {}
            cmd = args.get("cmd") or args.get("command") or ""
            if not isinstance(cmd, str) or not cmd.strip():
                continue
            for label, pat in DESTRUCTIVE:
                if re.search(pat, cmd):
                    out.append({"role": role, "phase": phase_of(path, role),
                                "kind": label, "cmd": cmd.strip()[:160],
                                "turn": d.get("turn")})
                    break
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(
        REPO, "shared/ablation_results/budget_sweep/core_tasks"))
    ap.add_argument("--model", default="gemini3flashpreview")
    ap.add_argument("--out", default=os.path.join(
        REPO, "shared/paper/quality/damage_attribution.json"))
    a = ap.parse_args()

    sp = importlib.util.spec_from_file_location(
        "bc", os.path.join(REPO, "scripts", "budget_curve.py"))
    bc = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(bc)
    base = bc.load_baseline()

    runs = []
    for cp in sorted(glob.glob(os.path.join(a.dir, "*%s*.checkpoint.jsonl" % a.model))):
        b = int(re.search(r"budget(\d+)_", os.path.basename(cp)).group(1))
        for line in open(cp):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("error"):
                continue
            t = r.get("task_id")
            if t not in base:
                continue
            adm, _ = bc.rescore(bc.checks_for(r), base[t])
            rd = r.get("run_dir") or ""
            if os.path.isdir(rd):
                runs.append({"budget": b, "cond": r.get("condition"),
                             "task": t, "guard_violated": not adm, "dir": rd})

    if not runs:
        print("no run directories found", file=sys.stderr)
        return 1

    per_role = collections.Counter()
    per_role_violating = collections.Counter()
    per_kind = collections.Counter()
    examples = collections.defaultdict(list)
    n_viol = 0
    for r in runs:
        if r["cond"] != "full":
            continue
        ev = scan_run(r["dir"])
        for e in ev:
            per_role[(e["role"], e["phase"])] += 1
            per_kind[e["kind"]] += 1
            if r["guard_violated"]:
                per_role_violating[e["role"]] += 1
                if len(examples[e["role"]]) < 3:
                    examples[e["role"]].append(
                        {"task": r["task"], "budget": r["budget"], **e})
        if r["guard_violated"]:
            n_viol += 1

    res = {
        "model": a.model,
        "team_runs_scanned": sum(1 for r in runs if r["cond"] == "full"),
        "team_runs_with_guard_violation": n_viol,
        "destructive_calls_by_role_phase": {
            "%s/%s" % k: v for k, v in sorted(per_role.items(), key=lambda kv: -kv[1])},
        "destructive_calls_by_role_in_violating_runs": dict(per_role_violating),
        "by_kind": dict(per_kind.most_common()),
        "examples": {k: v for k, v in examples.items()},
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)

    print("team runs scanned: %d, of which %d tripped a guard"
          % (res["team_runs_scanned"], n_viol))
    print("\nNOTE: these count workspace-mutating commands, which is how agents")
    print("edit. Use them for attribution across roles, not as a damage rate.")
    print("\nmutating calls by role and phase:")
    for k, v in res["destructive_calls_by_role_phase"].items():
        print("  %-34s %5d" % (k, v))
    print("\nin the runs that tripped a guard, by role:")
    for k, v in sorted(per_role_violating.items(), key=lambda kv: -kv[1]):
        print("  %-12s %5d" % (k, v))
    print("\nby kind:")
    for k, v in res["by_kind"].items():
        print("  %-22s %5d" % (k, v))
    print("\nwrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
