"""Stage TeamBench-Core tasks from upstream, and hold out their tests.

Two defects in the GH corpus are fixed here, both structural.

1. The scraper copied only the files a pull request touched, so a task's
   workspace is a fragment: conftest.py absent on 541 of 553 tasks with tests,
   packages in pieces ("No module named 'spacy.util'"), test-only dependencies
   missing. The grader's test target could not be collected, which is why no GH
   task passed under any model and the maintainers' own merged fix was worth
   +2.0 pp. A task is therefore staged by CHECKING OUT `repo` at `base_sha`.
   That also removes a licensing problem the copying created: 645 vendored
   workspaces ship zero upstream LICENSE files and the upstreams include
   AGPL-3.0, GPL-3.0 and LGPL-3.0 projects.

2. The test that defines the bug is the one the PR adds, and base_sha does not
   have it. Measured across the 229 tasks whose patch adds a test:

       189   the test file is present WITHOUT the added test
              -> the grader cannot distinguish any two submissions
        40   the added test is sitting in the workspace
              -> the agent can read the acceptance criterion

   So the only tasks that could ever discriminate were the ones that leaked the
   answer. Staging from base_sha removes the leak; the tests are then INJECTED
   at grade time, which is what SWE-bench does.

   The injected files are precomputed at stage time and copied over the
   workspace when grading, rather than patched in. Copying is deterministic and,
   more importantly, it overwrites whatever the agent did to those files, so
   weakening a test cannot raise a score.
"""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(REPO, "shared", "paper", "quality")
# Local disk, not the repository. The docker sandbox cannot bind-mount anything
# under this repo (NFS with root_squash denies the daemon's mkdir), so a cache
# kept there is invisible to the agent's shell. Everything the container needs
# has to live somewhere mountable, at the SAME absolute path inside and out.
CACHE = os.environ.get("TEAMBENCH_CORE_CACHE") or os.path.join(
    tempfile.gettempdir(), "teambench_core")
META_NAME = "core_env.json"

_CORE = None


def _sh(cmd, cwd=None, timeout=1800, env=None):
    return subprocess.run(cmd, shell=isinstance(cmd, str), cwd=cwd,
                          capture_output=True, text=True, timeout=timeout,
                          env={**os.environ, **(env or {})})


def load_core() -> dict:
    """Verified rows from every shard of build_verified_core.py, newest wins.

    A row carrying `env_freeze` is never replaced by one without it: the earliest
    shards predate the freeze, and staging from such a row installs almost no
    dependencies.
    """
    global _CORE
    if _CORE is not None:
        return _CORE
    out: dict = {}
    for p in sorted(glob.glob(os.path.join(Q, "verified_core*.json")),
                    key=os.path.getmtime):
        try:
            rows = json.load(open(p))
        except Exception:
            continue
        for r in rows:
            if not r.get("verified"):
                continue
            prev = out.get(r["task"])
            if prev and prev.get("env_freeze") and not r.get("env_freeze"):
                continue
            out[r["task"]] = r
    _CORE = out
    return out


def is_core_task(task_name: str) -> bool:
    return task_name in load_core()


def source_roots(ws: str) -> list:
    """Paths that make the checkout importable.

    `src/` is a layout detail, but without it `import marshmallow` fails from the
    workspace root and the grader's import check goes red for a reason that has
    nothing to do with the submission.
    """
    roots = [ws]
    src = os.path.join(ws, "src")
    if os.path.isdir(src) and any(
            os.path.isfile(os.path.join(src, d, "__init__.py"))
            for d in os.listdir(src) if os.path.isdir(os.path.join(src, d))):
        roots.insert(0, src)
    return roots


def deps_env(repo: str, sha: str) -> str:
    return os.path.join(CACHE, "deps", repo.replace("/", "_") + "@" + sha[:12])


def local_interpreter(recorded: str | None) -> str:
    """An interpreter that exists on local disk, copied out of the repo if needed.

    A venv records `home = <interpreter dir>` in pyvenv.cfg and its console
    scripts hardcode that path. If the interpreter lives on NFS the venv is
    unusable inside the sandbox, so the interpreter is mirrored into the same
    local cache as the dependency environments and the venv is built from there.
    """
    cache_py = os.path.join(CACHE, "python")
    if os.path.isfile(os.path.join(cache_py, "bin", "python3")):
        return os.path.join(cache_py, "bin", "python3")
    src = None
    if recorded and "/.cache/pythons/" in recorded and os.access(recorded, os.X_OK):
        src = os.path.dirname(os.path.dirname(recorded))
    else:
        pool = os.path.join(REPO, ".cache", "pythons")
        if os.path.isdir(pool):
            cands = sorted(os.listdir(pool), reverse=True)
            for c in cands:
                if os.access(os.path.join(pool, c, "bin", "python3"), os.X_OK):
                    src = os.path.join(pool, c)
                    break
    if not src:
        return sys.executable          # unsandboxed runs still work
    os.makedirs(CACHE, exist_ok=True)
    tmp = cache_py + ".partial"
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(src, tmp, symlinks=True)
    os.replace(tmp, cache_py)
    return os.path.join(cache_py, "bin", "python3")


def ensure_deps(row: dict, timeout: int = 1800) -> str:
    """Build the dependency environment once per (repo, base_sha).

    A venv, not `pip install --target`: the graders call the bare `pytest`
    console script, which a --target install does not create, so the run would
    fall through to whatever pytest is on PATH and measure the wrong
    environment. The venv lives at a fixed absolute path and is bind-mounted at
    that same path inside the sandbox, so nothing needs relocating.

    The package under test is deliberately NOT installed. `python -m pytest` from
    the workspace root puts the source tree first on sys.path, which is the copy
    the agent edits and the grader must measure.
    """
    d = deps_env(row["repo"], row["sha"])
    stamp = os.path.join(d, ".complete")
    if os.path.isfile(stamp):
        return d
    os.makedirs(os.path.dirname(d), exist_ok=True)
    base_py = local_interpreter(row.get("python"))
    _sh([base_py, "-m", "venv", d], timeout=timeout)
    pip = os.path.join(d, "bin", "pip")
    _sh([pip, "install", "-q", "-U", "pip", "setuptools", "wheel"], timeout=timeout)
    frozen = row.get("env_freeze") or ["pytest", "pytest-mock", "pytest-asyncio"]
    if _sh([pip, "install", "-q", *frozen], timeout=timeout).returncode:
        for pkg in frozen:
            _sh([pip, "install", "-q", pkg], timeout=timeout)
    open(stamp, "w").write("\n".join(frozen))
    return d


def _precompute_reference_tests(task: str, ws: str, dest: str) -> list:
    """Save each test file as the reference patch leaves it, then revert.

    Done here, with the patch and a clean tree in hand, so grading never has to
    apply a patch over whatever the agent wrote.
    """
    patch = os.path.join(REPO, "tasks", task, "reference", "patch.diff")
    if not os.path.isfile(patch):
        return []
    _sh(["git", "init", "-q"], cwd=ws)
    _sh(["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"], cwd=ws)
    _sh(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"],
        cwd=ws)
    r = _sh("git apply --include='*test*' %r" % patch, cwd=ws)
    saved = []
    if r.returncode == 0:
        out = _sh(["git", "diff", "--name-only"], cwd=ws)
        for rel in (out.stdout or "").split():
            src = os.path.join(ws, rel)
            if not os.path.isfile(src):
                continue
            dst = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            saved.append(rel)
    _sh(["git", "checkout", "-q", "--", "."], cwd=ws)
    _sh(["git", "clean", "-fdq"], cwd=ws)
    # The history is not part of the task, and leaving it would let an agent read
    # the fix out of a later commit.
    shutil.rmtree(os.path.join(ws, ".git"), ignore_errors=True)
    return saved


def stage(task: str, run_dir: str, timeout: int = 1800) -> dict | None:
    """Clone the task's upstream into <run_dir>/workspace. Returns the metadata."""
    row = load_core().get(task)
    if not row:
        return None
    ws = os.path.join(run_dir, "workspace")
    if os.path.isdir(ws):
        shutil.rmtree(ws)
    os.makedirs(run_dir, exist_ok=True)
    r = _sh(["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout",
             "https://github.com/%s.git" % row["repo"], ws], timeout=timeout)
    if r.returncode:
        return {"status": "clone_failed", "err": r.stderr[-200:]}
    r = _sh(["git", "checkout", "--quiet", row["sha"]], cwd=ws, timeout=timeout)
    if r.returncode:
        return {"status": "checkout_failed", "err": r.stderr[-200:]}
    held = os.path.join(run_dir, ".core", "reference_tests")
    os.makedirs(held, exist_ok=True)
    saved = _precompute_reference_tests(task, ws, held)
    meta = {"status": "ok", "task": task, "repo": row["repo"],
            "base_sha": row["sha"], "target": row.get("target"),
            "deps_env": ensure_deps(row, timeout),
            "reference_tests": saved,
            "source_roots": [os.path.relpath(p, run_dir) for p in source_roots(ws)]}
    json.dump(meta, open(os.path.join(run_dir, META_NAME), "w"), indent=1)
    return meta


def grade_prepare(run_dir: str) -> dict:
    """Inject the held-out tests and return the environment the grader needs.

    Returns {} for a task that was not staged from upstream, so the ordinary
    grading path is untouched.
    """
    p = os.path.join(run_dir, META_NAME)
    if not os.path.isfile(p):
        return {}
    try:
        meta = json.load(open(p))
    except Exception:
        return {}
    if meta.get("status") != "ok":
        return {}
    ws = os.path.abspath(os.path.join(run_dir, "workspace"))
    held = os.path.join(run_dir, ".core", "reference_tests")
    for rel in meta.get("reference_tests") or []:
        src = os.path.join(held, rel)
        if os.path.isfile(src):
            dst = os.path.join(ws, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    env = {}
    d = meta.get("deps_env") or ""
    if d and os.path.isdir(os.path.join(d, "bin")):
        env["PATH"] = os.path.join(d, "bin") + os.pathsep + os.environ.get("PATH", "")
    roots = [os.path.abspath(os.path.join(run_dir, r))
             for r in (meta.get("source_roots") or [])] or source_roots(ws)
    env["PYTHONPATH"] = os.pathsep.join(roots)
    return env
