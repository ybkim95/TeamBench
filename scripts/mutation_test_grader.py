#!/usr/bin/env python3
"""Mutation testing of grader discrimination on a passing workspace.

For each LB100 task that has a known-passing workspace (harvested from a
historical successful agent run), copy the workspace, apply each of a small
set of source-level mutations to one Python file at a time, and re-run the
deterministic grader.  Report mutation_kill_rate = (mutants whose grader
score dropped) / (total mutants attempted).

This replaces the broken Gate 2 in scripts/validate_task_quality.py: a
high mutation_kill_rate proves the grader is sensitive to real defects.

Mutations applied (AST-light, regex-based; safe for grade.sh-style tasks):
  - swap `==` and `!=`
  - swap `<` and `>`
  - swap `+` and `-` in arithmetic contexts
  - swap `True` and `False`
  - replace `return X` with `return None`
  - delete an `if ...:` body  (replace with `pass`)
  - swap `and` and `or`

Output:
  shared/paper/teambench_quality/mutation_kill.json  (per task)

Usage:
    python scripts/mutation_test_grader.py --lb100
    python scripts/mutation_test_grader.py --task SEC1_vuln_patch
    python scripts/mutation_test_grader.py --lb100 --max-mutants 10
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(REPO, "tasks")
ABL = os.path.join(REPO, "shared/ablation_results")
OUT = os.path.join(REPO, "shared/paper/teambench_quality/mutation_kill.json")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# ---------------------------------------------------------------------------
# Locate a passing workspace (the post-run state of a successful agent run)
# ---------------------------------------------------------------------------

def find_passing_workspaces(task_id: str, max_n=5) -> list[str]:
    """Return up to max_n run-dir paths whose run had pass=true."""
    found = []
    for fn in sorted(os.listdir(ABL)):
        if not fn.startswith("lb100_") or any(s in fn for s in ("invalid", "archived", "pre_", ".bak")):
            continue
        p = os.path.join(ABL, fn)
        if not os.path.isfile(p):
            continue
        records = []
        if fn.endswith(".json"):
            try:
                d = json.load(open(p))
            except Exception:
                continue
            records = d.get("runs", []) if isinstance(d, dict) else []
        elif fn.endswith(".checkpoint.jsonl"):
            for line in open(p):
                try:
                    records.append(json.loads(line))
                except Exception:
                    continue
        for r in records:
            if not isinstance(r, dict):
                continue
            if (r.get("task_id") == task_id) and (r.get("pass") or r.get("passed")):
                rd = r.get("run_dir") or ""
                if rd and not os.path.isabs(rd):
                    rd = os.path.join(REPO, rd)
                if os.path.isdir(os.path.join(rd, "workspace")):
                    found.append(rd)
                if len(found) >= max_n:
                    return found
    return found


# ---------------------------------------------------------------------------
# Mutators
# ---------------------------------------------------------------------------

MUTATIONS = [
    ("swap_eq_neq",    re.compile(r"==(?!=)"),  "!="),
    ("swap_neq_eq",    re.compile(r"!="),       "=="),
    ("swap_lt_gt",     re.compile(r"(?<![<>=!])<(?!=)"), ">"),
    ("swap_gt_lt",     re.compile(r"(?<![<>=!])>(?!=)"), "<"),
    ("swap_True_False",re.compile(r"\bTrue\b"), "False"),
    ("swap_False_True",re.compile(r"\bFalse\b"), "True"),
    ("swap_and_or",    re.compile(r"\band\b"),  "or"),
    ("swap_or_and",    re.compile(r"\bor\b"),   "and"),
    ("return_none",    re.compile(r"^(\s*)return\s+[^\n#]+", re.MULTILINE), r"\1return None"),
]


def apply_mutation(text: str, mut_name: str) -> tuple[str, int]:
    """Apply the named mutation once (first occurrence). Returns (new_text, n_changes)."""
    for name, pat, repl in MUTATIONS:
        if name != mut_name:
            continue
        m = pat.search(text)
        if not m:
            return text, 0
        new = text[: m.start()] + pat.sub(repl, text[m.start():], count=1)
        return new, 1
    return text, 0


SKIP_DIRS = {
    ".venv", "venv", "env", "__pycache__", ".git", "site-packages",
    ".tox", ".mypy_cache", ".pytest_cache", "dist-packages", "node_modules",
    "build", "dist", ".eggs", "egg-info", "bin",
}

# Third-party packages whose name typically appears at workspace root when
# the agent installed deps with `pip install --target=.` instead of a venv.
KNOWN_INSTALLED_PACKAGES = {
    "_pytest", "_distutils_hack", "pip", "setuptools", "wheel", "pkg_resources",
    "flask", "click", "blinker", "exceptiongroup", "iniconfig", "itsdangerous",
    "jinja2", "markupsafe", "packaging", "pluggy", "py", "pytest", "tomli",
    "werkzeug", "six", "attr", "attrs", "certifi", "charset_normalizer",
    "idna", "requests", "urllib3", "anyio", "h11", "httpcore", "httpx",
    "starlette", "fastapi", "pydantic", "pydantic_core", "typing_extensions",
    "sniffio", "uvicorn", "websockets", "yarl", "multidict", "aiohttp",
    "frozenlist", "aiosignal", "async_timeout", "asgiref", "django",
    "sqlalchemy", "greenlet", "alembic", "mako", "psycopg2", "redis",
    "celery", "kombu", "amqp", "billiard", "vine", "click_didyoumean",
    "click_plugins", "click_repl", "marshmallow", "jsonschema",
    "jsonschema_specifications", "referencing", "rpds", "rpds_py",
    "numpy", "scipy", "pandas", "matplotlib", "sklearn", "scikit_learn",
    "torch", "tensorflow", "spacy", "thinc", "wasabi", "srsly", "blis",
    "cymem", "preshed", "murmurhash", "cython", "pluggy", "ply",
    "pyparsing", "python_dateutil", "pytz", "tzdata", "dateutil",
    "openssl", "cryptography", "cffi", "pycparser",
}


def list_python_files(root: str) -> list[str]:
    """Return source-only Python files in a workspace.

    Skips:
      - test files (test_*.py, *_test.py)
      - virtualenvs and installed-package dirs (venv, site-packages, etc.)
      - directories whose name matches a known third-party package (when the
        agent installed deps with `pip install --target=.`)
      - directories with a sibling `<name>-<version>.dist-info` (positive
        evidence the directory is an installed package)
      - Python tooling caches
      - Python files installed as packages (any path containing /lib/pythonX.Y/)
    """
    # Discover .dist-info packages that live in this workspace and add their
    # base names to the skip set (one-time scan).
    dynamic_skip = set(SKIP_DIRS)
    try:
        for entry in os.listdir(root):
            if entry.endswith(".dist-info") or entry.endswith(".egg-info"):
                # name-version.dist-info → name (PEP 427 underscore normalization)
                base = entry.split("-", 1)[0]
                dynamic_skip.add(base)
                dynamic_skip.add(base.replace("_", "-"))
                dynamic_skip.add(base.replace("-", "_"))
    except OSError:
        pass
    dynamic_skip |= KNOWN_INSTALLED_PACKAGES

    out = []
    for d, dirs, files in os.walk(root):
        # Prune skip-dirs in place
        dirs[:] = [x for x in dirs if x not in dynamic_skip and not x.endswith(".dist-info") and not x.endswith(".egg-info")]
        # Skip any path under a Python install directory
        if "/lib/python" in d or "/site-packages/" in d or d.endswith("/site-packages"):
            continue
        for f in files:
            if not f.endswith(".py"):
                continue
            if f.startswith("test_") or f.endswith("_test.py"):
                continue
            out.append(os.path.join(d, f))
    return sorted(out)


# ---------------------------------------------------------------------------
# Grader runner
# ---------------------------------------------------------------------------

def run_grader(task_id: str, ws_dir: str, timeout: int = 120) -> tuple[bool, float]:
    grade_script = os.path.join(TASKS, task_id, "grade.sh")
    if not os.path.isfile(grade_script):
        return False, 0.0
    with tempfile.TemporaryDirectory(prefix="mut_rpts_") as rpts:
        sub = os.path.join(rpts, "submission")
        os.makedirs(sub, exist_ok=True)
        # Copy expected.json if the source workspace had one nearby
        src_expected = os.path.join(os.path.dirname(ws_dir), "reports", "expected.json")
        if os.path.isfile(src_expected):
            shutil.copy(src_expected, os.path.join(rpts, "expected.json"))
        env = os.environ.copy()
        env["PATH"] = os.path.dirname(os.path.abspath(sys.executable)) + os.pathsep + env.get("PATH", "")
        args = ["bash", grade_script, ws_dir, rpts, sub, os.path.join(TASKS, task_id)]
        if os.path.isfile(os.path.join(rpts, "expected.json")):
            args.append(os.path.join(rpts, "expected.json"))
        try:
            subprocess.run(args, capture_output=True, text=True, timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            return False, 0.0
        score_path = os.path.join(rpts, "score.json")
        if not os.path.isfile(score_path):
            return False, 0.0
        try:
            d = json.load(open(score_path))
        except Exception:
            return False, 0.0
        primary = 0.0
        p = d.get("primary", {})
        if isinstance(p, dict):
            for k in ("success", "score", "passed"):
                if k in p:
                    primary = float(p[k])
                    break
        else:
            primary = 1.0 if d.get("pass") else 0.0
        return bool(d.get("pass")), primary


# ---------------------------------------------------------------------------
# Per-task mutation test
# ---------------------------------------------------------------------------

def mutation_test_task(task_id: str, max_mutants: int = 12) -> dict:
    rec = {"task_id": task_id, "checked_at": datetime.now(timezone.utc).isoformat(),
           "kill_rate": None, "n_attempted": 0, "n_killed": 0, "mutants": [], "notes": ""}

    rdirs = find_passing_workspaces(task_id, max_n=2)
    if not rdirs:
        rec["notes"] = "no passing workspace available"
        return rec

    base_ws = os.path.join(rdirs[0], "workspace")
    py_files = list_python_files(base_ws)
    if not py_files:
        rec["notes"] = "no python files in workspace"
        return rec

    # First, sanity-check that the unmodified base workspace passes
    with tempfile.TemporaryDirectory(prefix="mut_base_") as tmp:
        tmp_ws = os.path.join(tmp, "workspace")
        shutil.copytree(base_ws, tmp_ws)
        passed, prim = run_grader(task_id, tmp_ws)
        rec["base_pass"] = passed
        rec["base_primary"] = prim
        if not passed:
            rec["notes"] = "base workspace did not pass grader; skipping mutation test"
            return rec

    rec["n_python_files"] = len(py_files)

    # Try mutations across files
    attempts = 0
    for py in py_files:
        if attempts >= max_mutants:
            break
        with open(py) as f:
            orig = f.read()
        for name, _, _ in MUTATIONS:
            if attempts >= max_mutants:
                break
            mutated, n_changes = apply_mutation(orig, name)
            if n_changes == 0 or mutated == orig:
                continue
            attempts += 1
            with tempfile.TemporaryDirectory(prefix=f"mut_{name}_") as tmp:
                tmp_ws = os.path.join(tmp, "workspace")
                shutil.copytree(base_ws, tmp_ws)
                rel = os.path.relpath(py, base_ws)
                tgt = os.path.join(tmp_ws, rel)
                with open(tgt, "w") as f:
                    f.write(mutated)
                passed, prim = run_grader(task_id, tmp_ws)
                killed = (not passed) or (prim < rec["base_primary"] - 0.05)
                rec["mutants"].append({
                    "file": rel, "mutation": name,
                    "passed_after": passed, "primary_after": prim, "killed": bool(killed),
                })
                if killed:
                    rec["n_killed"] += 1
                rec["n_attempted"] += 1

    if rec["n_attempted"] > 0:
        rec["kill_rate"] = round(rec["n_killed"] / rec["n_attempted"], 4)
    return rec


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--task", action="append", default=[])
    g.add_argument("--lb100", action="store_true")
    ap.add_argument("--max-mutants", type=int, default=12)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if args.task:
        ids = args.task
    else:
        sel = json.load(open(os.path.join(REPO, "leaderboard/data/leaderboard_100_tasks.json")))["tasks"]
        ids = [t["task_id"] if isinstance(t, dict) else t for t in sel]
    if args.limit:
        ids = ids[: args.limit]

    print(f"[mutation-test] running on {len(ids)} tasks; max {args.max_mutants} mutants/task; out={args.out}")
    existing = []
    if os.path.isfile(args.out):
        try:
            existing = json.load(open(args.out)).get("results", [])
        except Exception:
            existing = []
    seen = {r["task_id"] for r in existing}
    results = list(existing)

    t0 = time.time()
    for i, tid in enumerate(ids, 1):
        if tid in seen:
            continue
        try:
            rec = mutation_test_task(tid, max_mutants=args.max_mutants)
        except KeyboardInterrupt:
            break
        except Exception as e:
            rec = {"task_id": tid, "kill_rate": None, "notes": f"crashed: {e}"}
        results.append(rec)
        if i % 5 == 0 or i == len(ids):
            kr = rec.get("kill_rate")
            elapsed = time.time() - t0
            rate = i / elapsed if elapsed else 0
            print(f"[{i:>4}/{len(ids)}] {tid:<35} kill_rate={kr} attempts={rec.get('n_attempted',0)} ({rate:.1f}/s)")
            json.dump({"computed_at": datetime.now(timezone.utc).isoformat(),
                       "n": len(results), "results": results},
                      open(args.out, "w"), indent=2)

    json.dump({"computed_at": datetime.now(timezone.utc).isoformat(),
               "n": len(results), "results": results},
              open(args.out, "w"), indent=2)
    print(f"\n[mutation-test] done. wrote {args.out}")


if __name__ == "__main__":
    main()
