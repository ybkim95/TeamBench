#!/usr/bin/env python3
"""Restore the conftest.py files the task scraper dropped.

Root cause of the GH corpus never passing anything
--------------------------------------------------
The scraper copied only the files a PR touched. conftest.py is almost never
touched by a bug-fix PR, so it was left behind: 541 of the 553 GH tasks that ship
a test file have no conftest.py, and 91% of those tests request a fixture. pytest
resolves fixtures from conftest.py, so the suite errors at collection:

    fixture 'lang_locales' not found

That is one grader check, C1 "test suite passes", failing for a reason that has
nothing to do with the submission. It is also the whole explanation for the
symptoms measured earlier:

  * no GH task passed in any condition, under any model
  * the upstream reference patch failed to reach 1.0 on 150 of 153 tasks
  * applying the maintainers' own merged fix was worth only +2.0 pp
  * the rebuilt budget sweep returned binary pass 0 of 100

Traced on GH444_arrow_1184: with the reference applied, C9 and C10 flip from FAIL
to OK, so the fix itself is recognised. Only C1 stays red, and only because
tests/conftest.py is absent.

This fetches each task's conftest.py chain from the upstream repo at its recorded
base_sha and writes it into the workspace. It adds files the task always needed to
run; it does not touch the grader, the spec, the reference patch, or any recorded
result.

Usage:
  python scripts/fetch_missing_conftest.py --dry-run
  python scripts/fetch_missing_conftest.py --apply
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import glob
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(REPO, "tasks")
API = "https://api.github.com"
TEST_RE = re.compile(r"(^|/)(test_[^/]*|[^/]*_test)\.py$")


def load_token() -> str:
    tok = os.environ.get("GITHUB_TOKEN", "")
    if tok:
        return tok
    env = os.path.join(REPO, ".env")
    if os.path.isfile(env):
        for line in open(env, encoding="utf-8", errors="ignore"):
            if line.startswith("GITHUB_TOKEN="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return ""


TOKEN = load_token()


def gh(url: str, retries: int = 4):
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "teambench-conftest",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in (403, 429) and attempt < retries - 1:
                reset = e.headers.get("X-RateLimit-Reset")
                wait = 60
                if reset:
                    wait = max(5, min(900, int(reset) - int(time.time()) + 5))
                time.sleep(wait)
                continue
            if attempt == retries - 1:
                return None
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(2 ** attempt)
    return None


def conftest_candidates(test_rel: str) -> list[str]:
    """Every directory from the test file up to the repo root, as pytest searches."""
    parts = test_rel.split("/")[:-1]
    out = []
    for i in range(len(parts), -1, -1):
        out.append("/".join(parts[:i] + ["conftest.py"]) if i else "conftest.py")
    return out


def process(task: str, apply: bool) -> dict:
    ws = os.path.join(TASKS, task, "workspace")
    notes_p = os.path.join(TASKS, task, "curation_notes.json")
    if not os.path.isdir(ws) or not os.path.isfile(notes_p):
        return {"task": task, "status": "no_workspace_or_notes"}
    if glob.glob(os.path.join(ws, "**", "conftest.py"), recursive=True):
        return {"task": task, "status": "already_has_conftest"}
    tests = [p for p in glob.glob(os.path.join(ws, "**", "*.py"), recursive=True)
             if TEST_RE.search(p.replace(os.sep, "/"))]
    if not tests:
        return {"task": task, "status": "no_test_file"}
    try:
        n = json.load(open(notes_p))
    except Exception:
        return {"task": task, "status": "bad_notes"}
    repo, sha = n.get("repo"), n.get("base_sha")
    if not repo or not sha:
        return {"task": task, "status": "no_repo_or_sha"}

    rel = os.path.relpath(tests[0], ws).replace(os.sep, "/")
    written = []
    for cand in conftest_candidates(rel):
        j = gh(f"{API}/repos/{repo}/contents/{cand}?ref={sha}")
        if not isinstance(j, dict) or j.get("type") != "file":
            continue
        import base64
        try:
            content = base64.b64decode(j.get("content", "")).decode("utf-8", "replace")
        except Exception:
            continue
        if apply:
            dest = os.path.join(ws, *cand.split("/"))
            os.makedirs(os.path.dirname(dest) or ws, exist_ok=True)
            with open(dest, "w", encoding="utf-8", newline="") as f:
                f.write(content)
        written.append(cand)
    if not written:
        return {"task": task, "status": "no_conftest_upstream", "repo": repo}
    return {"task": task, "status": "ok", "repo": repo, "files": written}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    if not TOKEN:
        print("no GITHUB_TOKEN; unauthenticated requests cap at 60/hour", file=sys.stderr)

    tasks = [d for d in sorted(os.listdir(TASKS))
             if d.startswith("GH") and os.path.isdir(os.path.join(TASKS, d, "workspace"))]
    if a.limit:
        tasks = tasks[: a.limit]
    print(f"GH tasks with a workspace: {len(tasks)}", flush=True)

    res = []
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(process, t, a.apply and not a.dry_run): t for t in tasks}
        for i, fut in enumerate(cf.as_completed(futs), 1):
            res.append(fut.result())
            if i % 50 == 0:
                c = collections.Counter(r["status"] for r in res)
                print(f"  [{i}/{len(tasks)}] {dict(c)}", flush=True)

    c = collections.Counter(r["status"] for r in res)
    print("\nresult:")
    for k, v in c.most_common():
        print(f"  {k:24} {v}")
    nf = sum(len(r.get("files", [])) for r in res)
    print(f"\n  conftest files {'written' if a.apply and not a.dry_run else 'that WOULD be written'}: {nf}")
    out = os.path.join(REPO, "shared", "paper", "quality", "conftest_restore.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w"), indent=1)
    print(f"  report: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
