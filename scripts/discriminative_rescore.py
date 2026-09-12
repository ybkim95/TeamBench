#!/usr/bin/env python3
"""Score only the checks that a solution can actually change.

Measured: 365 of 593 checks (61.6%) pass on an untouched workspace, and the mean
do-nothing partial score is 0.551. Guard checks ("source still parses", "tests not
deleted", "file has at least N lines", "no cheat markers") sit in both the
numerator and the denominator of partial_score, so most of every reported score
is credit for not vandalising the workspace.

The fix does not remove the guards, which do real anti-cheat work. It moves them
out of the score:

    admissible   = every guard check passes        (pass/fail, not scored)
    partial      = passed discriminative / all discriminative

A check is discriminative FOR A TASK iff it fails on that task's pristine
workspace. That is a per-(task, check) property, not a property of the check's
name: "source modules import without error" is a guard on one task and the whole
point of another. Classifying by name would be wrong on both.

Stage 1 (--baseline) records each task's pristine checklist.
Stage 2 (--rescore) recomputes stored run scores against it. No model is called;
every run's own checklist is already in its score.json, so this is arithmetic on
existing artifacts.

A task whose discriminative set is empty cannot distinguish a solution from an
empty submission and is reported as inadmissible rather than silently scored 1.0.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(REPO, "tasks")
Q = os.path.join(REPO, "shared", "paper", "quality")
BASELINE = os.path.join(Q, "pristine_checks.json")


def check_key(c: dict) -> str:
    """Stable identity for a check within a task."""
    return str(c.get("id") or "") + "|" + str(c.get("note") or "")[:80]


def stage_workspace(task: str, dest: str) -> bool:
    static = os.path.join(TASKS, task, "workspace")
    if os.path.isdir(static) and os.listdir(static):
        shutil.copytree(static, dest, dirs_exist_ok=True)
        return True
    # Generator-backed tasks are staged in a SUBPROCESS. Importing
    # generators.registry pulls in ~1500 modules, and at least one of them
    # brings a native extension into a state where cryptography's pyo3 bindings
    # abort the interpreter with a PanicException. That kills the whole sweep,
    # and a panic cannot be caught with `except Exception`, so isolation is the
    # only reliable containment.
    helper = (
        "import sys, os, json\n"
        "sys.path.insert(0, %r)\n"
        "from generators.registry import get_generator\n"
        "res = get_generator(%r).generate(seed=0)\n"
        "files = dict(getattr(res, 'workspace_files', None) or {})\n"
        "files.update(getattr(res, 'corpus_files', None) or {})\n"
        "dest = %r\n"
        "for rel, content in files.items():\n"
        "    p = os.path.join(dest, rel)\n"
        "    os.makedirs(os.path.dirname(p) or dest, exist_ok=True)\n"
        "    mode = 'wb' if isinstance(content, bytes) else 'w'\n"
        "    open(p, mode).write(content)\n"
        "print(len(files))\n"
    ) % (REPO, task.lower(), dest)
    try:
        r = subprocess.run([sys.executable, "-c", helper], capture_output=True,
                           text=True, timeout=120, cwd=REPO)
        return r.returncode == 0 and (r.stdout or "0").strip().isdigit() \
            and int(r.stdout.strip()) > 0
    except Exception:
        return False


def pristine_checklist(task: str, timeout: int):
    run = tempfile.mkdtemp(prefix="disc_")
    try:
        ws = os.path.join(run, "workspace")
        os.makedirs(ws)
        if not stage_workspace(task, ws):
            return None
        for d in ("reports", "submission"):
            os.makedirs(os.path.join(run, d))
        json.dump({"task_id": task, "verdict": "pass", "checklist": []},
                  open(os.path.join(run, "submission", "attestation.json"), "w"))
        try:
            subprocess.run(["bash", os.path.join(TASKS, task, "grade.sh"), ws,
                            os.path.join(run, "reports"), os.path.join(run, "submission"),
                            os.path.join(TASKS, task)],
                           capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return None
        p = os.path.join(run, "reports", "score.json")
        if not os.path.isfile(p):
            return None
        sc = json.load(open(p))
        sec = sc.get("secondary") or {}
        checks = sec.get("checks") or sc.get("checklist") or []
        if not checks:
            return None
        return {"free": [check_key(c) for c in checks if isinstance(c, dict) and c.get("ok")],
                "all": [check_key(c) for c in checks if isinstance(c, dict)],
                "pristine_partial": sec.get("partial_score")}
    finally:
        shutil.rmtree(run, ignore_errors=True)


def rescore(checks: list, base: dict):
    """Return (admissible, partial_discriminative, n_disc, n_guard)."""
    free = set(base["free"])
    guard_ok, passed, n_disc = True, 0, 0
    for c in checks:
        if not isinstance(c, dict):
            continue
        k = check_key(c)
        if k in free:                       # guard: must hold, never scored
            guard_ok &= bool(c.get("ok"))
        else:                               # discriminative: this is the score
            n_disc += 1
            passed += bool(c.get("ok"))
    if n_disc == 0:
        return guard_ok, None, 0, len(free)
    return guard_ok, passed / n_disc, n_disc, len(free)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true")
    ap.add_argument("--rescore", action="store_true")
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    os.makedirs(Q, exist_ok=True)

    if a.baseline:
        tasks = [d for d in sorted(os.listdir(TASKS))
                 if os.path.isfile(os.path.join(TASKS, d, "grade.sh"))]
        if a.limit:
            tasks = tasks[: a.limit]
        base = {}
        if os.path.isfile(BASELINE):
            base = json.load(open(BASELINE))
            print(f"resuming, {len(base)} tasks already baselined", flush=True)
        todo = [t for t in tasks if t not in base]
        print(f"tasks with a grader: {len(tasks)}; to baseline: {len(todo)}", flush=True)
        for i, t in enumerate(todo, 1):
            r = pristine_checklist(t, a.timeout)
            if r:
                base[t] = r
            if i % 40 == 0:
                json.dump(base, open(BASELINE, "w"))
                print(f"  {i}/{len(todo)}  baselined={len(base)}", flush=True)
        json.dump(base, open(BASELINE, "w"))
        empt = sum(1 for v in base.values() if len(v["free"]) == len(v["all"]))
        print(f"\nbaselined {len(base)} tasks")
        print(f"  tasks with NO discriminative check at all: {empt} "
              f"({100*empt/max(1,len(base)):.1f}%)  <- cannot distinguish a solution")
        print(f"wrote {BASELINE}")
        return 0

    if a.rescore:
        if not os.path.isfile(BASELINE):
            print("run --baseline first", file=sys.stderr)
            return 2
        base = json.load(open(BASELINE))
        base_lower = {k.lower(): k for k in base}
        rows, skipped = [], collections.Counter()
        for sp in glob.glob(os.path.join(REPO, "shared", "**", "score.json"), recursive=True):
            try:
                sc = json.load(open(sp))
            except Exception:
                skipped["unreadable"] += 1
                continue
            sec = sc.get("secondary") or {}
            checks = sec.get("checks") or sc.get("checklist") or []
            # Resolve the task three ways. Path-component matching alone missed
            # 453 runs whose directory is named for the campaign rather than the
            # task (shared/ablation_runs/<ts>/...), and score.json almost always
            # names its own task, which the first version never consulted.
            task = None
            parts = sp.split(os.sep)
            for p in parts:
                if p in base:
                    task = p
                    break
            if task is None:
                named = sc.get("task_id") or sc.get("task")
                if named:
                    task = base_lower.get(str(named).lower())
            if not task or not checks:
                skipped["no_task_or_checks"] += 1
                continue
            adm, part, nd, ng = rescore(checks, base[task])
            rows.append({"score_json": sp, "task": task,
                         "old_partial": sec.get("partial_score"),
                         "old_pass": bool(sc.get("pass")),
                         "admissible": adm, "new_partial": part,
                         "n_discriminative": nd, "n_guard": ng})
        json.dump(rows, open(os.path.join(Q, "rescored_runs.json"), "w"), indent=1)
        import statistics
        old = [r["old_partial"] for r in rows if isinstance(r["old_partial"], (int, float))]
        new = [r["new_partial"] for r in rows if isinstance(r["new_partial"], (int, float))]
        print(f"rescored runs: {len(rows)}   skipped: {dict(skipped)}")
        if old:
            print(f"  old mean partial: {statistics.mean(old):.3f}")
        if new:
            print(f"  new mean partial: {statistics.mean(new):.3f}  (n={len(new)})")
        nod = sum(1 for r in rows if r["n_discriminative"] == 0)
        print(f"  runs on tasks with no discriminative check: {nod}")
        inad = sum(1 for r in rows if not r["admissible"])
        print(f"  runs failing a guard (inadmissible): {inad}")
        print(f"\nwrote {os.path.join(Q,'rescored_runs.json')}")
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
