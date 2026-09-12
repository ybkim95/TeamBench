#!/usr/bin/env python3
"""
Parameterisation corruption scan
================================

    python3 scripts/param_corruption_scan.py --out shared/paper/quality/param_corruption.json

``generators/gh_deep_param.py`` renames "user-defined" identifiers to make GH
task instances seed-specific.  Its exclusion list for Python builtins is built as

    _PYTHON_BUILTINS = frozenset(dir(__builtins__) if isinstance(__builtins__, dict)
                                 else dir(__builtins__))

Inside an imported module ``__builtins__`` is the builtins **dict**, so
``dir()`` of it returns the dict's own 45 methods (``__contains__``,
``__getitem__``, ...) and not a single builtin name.  ``set``, ``str``, ``len``,
``dict`` and every other builtin are therefore treated as user symbols and get a
seed suffix.  The same happens to names imported from the standard library:
``_STDLIB_MODULES`` holds module names, not the symbols imported out of them, so
``from contextlib import contextmanager`` becomes
``from contextlib import contextmanager_ext``.

The result is a workspace that still parses but cannot import.  This script
measures how far that reaches, without executing any task code:

  builtin_rename    a NAME token of the form ``<builtin><suffix>`` is used and is
                    bound nowhere in the file
  bad_stdlib_import ``from <stdlib module> import X`` where X is not an attribute
                    of that module in this interpreter

Both are decisive: either one means the file raises on import, so every grader
check that imports or runs it fails no matter what an agent writes.
"""
from __future__ import annotations

import argparse
import ast
import builtins
import importlib
import json
import os
import sys
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

SUFFIXES = ("_v2", "_impl", "_new", "_base", "_core", "_alt", "_ext", "_mod")
BUILTINS = {b for b in dir(builtins) if not b.startswith("_")}
STDLIB = {
    "os", "sys", "re", "io", "abc", "ast", "collections", "contextlib", "copy",
    "dataclasses", "datetime", "enum", "functools", "hashlib", "heapq",
    "inspect", "itertools", "json", "logging", "math", "operator", "pathlib",
    "pickle", "queue", "random", "shutil", "signal", "socket", "string",
    "struct", "subprocess", "tempfile", "threading", "time", "traceback",
    "typing", "unittest", "urllib", "uuid", "warnings", "weakref", "textwrap",
    "types", "numbers", "decimal", "fractions", "statistics", "base64",
    "binascii", "codecs", "csv", "glob", "gzip", "importlib", "keyword",
    "platform", "pprint", "secrets", "select", "shlex", "stat", "tokenize",
    "unicodedata", "zlib", "asyncio", "concurrent", "email", "http", "ssl",
}
_MOD_CACHE: dict[str, object] = {}


def _module(name: str):
    if name not in _MOD_CACHE:
        try:
            _MOD_CACHE[name] = importlib.import_module(name)
        except Exception:
            _MOD_CACHE[name] = None
    return _MOD_CACHE[name]


def bound_names(tree: ast.AST) -> set[str]:
    out: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            out.add(n.id)
        elif isinstance(n, ast.arg):
            out.add(n.arg)
        elif isinstance(n, ast.alias):
            out.add((n.asname or n.name).split(".")[0])
        elif isinstance(n, ast.ExceptHandler) and n.name:
            out.add(n.name)
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            out.update(n.names)
    return out


def scan_source(src: str) -> dict:
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return {"parse_error": str(exc)[:120], "builtin_renames": [],
                "bad_stdlib_imports": []}
    bound = bound_names(tree)
    renamed = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            nm = n.id
            if nm in bound:
                continue
            for suf in SUFFIXES:
                if nm.endswith(suf) and nm[: -len(suf)] in BUILTINS:
                    renamed.add(nm)
                    break
    bad_imports = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            root = n.module.split(".")[0]
            if root not in STDLIB:
                continue
            mod = _module(n.module)
            if mod is None:
                continue
            for a in n.names:
                if a.name == "*":
                    continue
                if not hasattr(mod, a.name):
                    bad_imports.append(f"{n.module}.{a.name}")
    return {"parse_error": None, "builtin_renames": sorted(renamed),
            "bad_stdlib_imports": sorted(set(bad_imports))}


def scan_task(task_id: str, seed: int, runs_root: str) -> dict:
    from harness.run_all import setup_run
    rec = {"task_id": task_id, "seed": seed, "py_files": 0, "files_corrupt": 0,
           "builtin_renames": [], "bad_stdlib_imports": [], "parse_errors": 0,
           "error": None}
    run_dir = None
    try:
        _rid, run_dir, _td = setup_run(task_id, os.path.join(REPO_ROOT, "tasks"),
                                       runs_root, seed=seed)
        ws = os.path.join(run_dir, "workspace")
        for root, dirs, files in os.walk(ws):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
            for f in files:
                if not f.endswith(".py"):
                    continue
                rec["py_files"] += 1
                try:
                    with open(os.path.join(root, f), encoding="utf-8",
                              errors="surrogateescape") as fh:
                        src = fh.read()
                except OSError:
                    continue
                s = scan_source(src)
                if s["parse_error"]:
                    # A .py the parameteriser rewrote into something that does
                    # not even parse is maximally corrupt, so it counts. This
                    # happens when the symbol pool is collected across ALL
                    # languages in the workspace: a Rust or TypeScript file
                    # contributes `from` or `class` as a "user symbol", and the
                    # Python renamer then rewrites those NAME tokens, producing
                    # `from_v2 decimal import ...` / `class_new MyModel(...)`.
                    rec["parse_errors"] += 1
                    rec["files_corrupt"] += 1
                    rec.setdefault("parse_error_samples", []).append(
                        {"file": os.path.relpath(os.path.join(root, f), ws),
                         "error": s["parse_error"]})
                elif s["builtin_renames"] or s["bad_stdlib_imports"]:
                    rec["files_corrupt"] += 1
                rec["builtin_renames"] += s["builtin_renames"]
                rec["bad_stdlib_imports"] += s["bad_stdlib_imports"]
    except Exception as exc:
        rec["error"] = f"{type(exc).__name__}: {exc}"[:200]
    finally:
        if run_dir:
            shutil.rmtree(run_dir, ignore_errors=True)
    rec["builtin_renames"] = sorted(set(rec["builtin_renames"]))[:40]
    rec["bad_stdlib_imports"] = sorted(set(rec["bad_stdlib_imports"]))[:40]
    rec["corrupt"] = bool(rec["files_corrupt"])
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(
        REPO_ROOT, "shared", "paper", "quality", "param_corruption.json"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--tasks", nargs="*", default=None)
    ap.add_argument("--only-with-reference", action="store_true")
    args = ap.parse_args()

    tasks_dir = os.path.join(REPO_ROOT, "tasks")
    if args.tasks:
        ids = args.tasks
    else:
        ids = sorted(d for d in os.listdir(tasks_dir)
                     if os.path.isfile(os.path.join(tasks_dir, d, "grade.sh")))
        if args.only_with_reference:
            ids = [t for t in ids
                   if os.path.isfile(os.path.join(tasks_dir, t, "reference", "patch.diff"))]
    runs_root = tempfile.mkdtemp(prefix="paramscan_", dir=os.environ.get("TMPDIR", "/tmp"))
    recs = []
    try:
        with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 8))) as pool:
            futs = {pool.submit(scan_task, t, args.seed, runs_root): t for t in ids}
            for i, fut in enumerate(as_completed(futs), 1):
                recs.append(fut.result())
                if i % 50 == 0:
                    print(f"[{i}/{len(ids)}]", flush=True)
    finally:
        shutil.rmtree(runs_root, ignore_errors=True)

    recs.sort(key=lambda r: r["task_id"])
    n = len(recs)
    corrupt = [r for r in recs if r["corrupt"]]
    from collections import Counter
    fam = Counter(r["task_id"].rstrip("0123456789").split("_")[0] for r in corrupt)
    names = Counter()
    for r in corrupt:
        names.update(r["builtin_renames"])
    imports = Counter()
    for r in corrupt:
        imports.update(r["bad_stdlib_imports"])
    summary = {
        "n_tasks": n,
        "tasks_with_corrupt_python": len(corrupt),
        "frac": round(len(corrupt) / n, 4) if n else None,
        "total_py_files": sum(r["py_files"] for r in recs),
        "corrupt_py_files": sum(r["files_corrupt"] for r in recs),
        "tasks_with_parse_errors": sum(1 for r in recs if r["parse_errors"]),
        "errors": sum(1 for r in recs if r["error"]),
        "most_common_renamed_builtins": names.most_common(25),
        "most_common_bad_stdlib_imports": imports.most_common(25),
        "by_family_prefix": dict(fam.most_common()),
        "seed": args.seed,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "tasks": recs}, f, indent=2)
    print(json.dumps(summary, indent=2)[:2500])
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
