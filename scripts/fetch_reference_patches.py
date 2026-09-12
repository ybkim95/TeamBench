#!/usr/bin/env python3
"""Fetch the authoritative reference patch for every GitHub-sourced task.

Why this exists
---------------
The admission gate's G3 ("a known-correct solution passes the grader") is the
SWE-bench-Verified-style check that turns a task dump into a validated benchmark.
It was `unknown` for 128 of 150 evaluated tasks because no reference solution
existed, and `fail` for all 22 that did.

`scripts/deleak_specs.py` salvaged 296 patches out of the ```diff blocks that had
been leaking inside spec.md, but 83 of those were truncated mid-hunk by the
original scraper and 337 de-leaked tasks never carried a diff at all. This script
goes to the source instead: every GH task's curation_notes.json records `repo`,
`pr_number` and `head_sha`, so the real unified diff can be fetched from the
GitHub API and stored as the grader-only oracle.

Output per task, under tasks/<id>/reference/:
  patch.diff        the upstream unified diff
  patch_meta.json   provenance: repo, pr, base_sha, head_sha, source, sizes

Never writes anything an agent role can read: harness/agent_interface.py denies
every path with a `reference` component (ReadFileTool.denied_dirs).

Usage:
  python3 scripts/fetch_reference_patches.py --dry-run     # inventory only
  python3 scripts/fetch_reference_patches.py               # fetch missing/truncated
  python3 scripts/fetch_reference_patches.py --all         # refetch everything
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(ROOT, "tasks")
API = "https://api.github.com"


def load_token() -> str:
    tok = os.environ.get("GITHUB_TOKEN", "")
    if tok:
        return tok
    env = os.path.join(ROOT, ".env")
    if os.path.isfile(env):
        for line in open(env, encoding="utf-8", errors="ignore"):
            if line.startswith("GITHUB_TOKEN="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return ""


TOKEN = load_token()


def gh(url: str, accept: str = "application/vnd.github+json", retries: int = 4):
    """GET with auth, honouring secondary-rate-limit backoff."""
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={
            "Accept": accept,
            "User-Agent": "teambench-reference-fetch",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                reset = e.headers.get("X-RateLimit-Reset")
                wait = 60
                if reset:
                    wait = max(5, min(900, int(reset) - int(time.time()) + 5))
                if attempt < retries - 1:
                    time.sleep(wait)
                    continue
            if e.code == 404:
                return None, {"error": "404"}
            if attempt == retries - 1:
                return None, {"error": f"HTTP {e.code}"}
            time.sleep(2 ** attempt)
        except Exception as e:  # network flake
            if attempt == retries - 1:
                return None, {"error": str(e)[:120]}
            time.sleep(2 ** attempt)
    return None, {"error": "exhausted"}


def task_needs_patch(task: str, refetch_all: bool) -> tuple[bool, str]:
    ref = os.path.join(TASKS, task, "reference")
    meta_p = os.path.join(ref, "patch_meta.json")
    diff_p = os.path.join(ref, "patch.diff")
    if refetch_all:
        return True, "refetch-all"
    if not os.path.isfile(diff_p):
        return True, "missing"
    if os.path.isfile(meta_p):
        try:
            if not json.load(open(meta_p)).get("complete", False):
                return True, "truncated"
        except Exception:
            return True, "unreadable-meta"
    return False, "present"


def fetch_one(task: str, reason: str) -> dict:
    notes_p = os.path.join(TASKS, task, "curation_notes.json")
    if not os.path.isfile(notes_p):
        return {"task": task, "status": "no_curation_notes", "reason": reason}
    try:
        n = json.load(open(notes_p))
    except Exception as e:
        return {"task": task, "status": "bad_curation_notes", "error": str(e)[:80]}

    repo, pr = n.get("repo"), n.get("pr_number")
    if not repo or not pr:
        return {"task": task, "status": "no_repo_or_pr", "repo": repo, "pr": pr}

    body, _ = gh(f"{API}/repos/{repo}/pulls/{pr}",
                 accept="application/vnd.github.v3.diff")
    if body is None:
        return {"task": task, "status": "fetch_failed", "repo": repo, "pr": pr}

    diff = body.decode("utf-8", errors="replace")
    if not diff.strip():
        return {"task": task, "status": "empty_diff", "repo": repo, "pr": pr}

    ref = os.path.join(TASKS, task, "reference")
    os.makedirs(ref, exist_ok=True)
    with open(os.path.join(ref, "patch.diff"), "w", encoding="utf-8", newline="") as f:
        f.write(diff)
    meta = {
        "task": task, "patch": f"tasks/{task}/reference/patch.diff",
        "complete": True, "problems": [],
        "source": "github_api_pull_diff",
        "repo": repo, "pr_number": pr,
        "base_sha": n.get("base_sha"), "head_sha": n.get("head_sha"),
        "bytes": len(diff), "files_changed": diff.count("\ndiff --git ") + diff.startswith("diff --git "),
        "fetched_reason": reason,
        "note": ("Authoritative upstream diff fetched from the GitHub API. "
                 "GRADER-ONLY: harness ReadFileTool denies any path containing a "
                 "'reference' component, so no agent role can read this."),
    }
    with open(os.path.join(ref, "patch_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    return {"task": task, "status": "ok", "bytes": len(diff),
            "files_changed": meta["files_changed"], "reason": reason}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all", action="store_true", help="refetch even complete patches")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    if not TOKEN:
        print("No GITHUB_TOKEN found; unauthenticated requests are limited to 60/hour.",
              file=sys.stderr)

    tasks = sorted(d for d in os.listdir(TASKS)
                   if d.startswith("GH")
                   and os.path.isfile(os.path.join(TASKS, d, "curation_notes.json")))
    todo = [(t, r) for t in tasks for need, r in [task_needs_patch(t, a.all)] if need]
    if a.limit:
        todo = todo[:a.limit]

    from collections import Counter
    print(f"GH tasks with curation notes : {len(tasks)}")
    print(f"needing a reference patch    : {len(todo)}  {dict(Counter(r for _, r in todo))}")
    if a.dry_run or not todo:
        return 0

    results = []
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(fetch_one, t, r): t for t, r in todo}
        for i, fut in enumerate(cf.as_completed(futs), 1):
            results.append(fut.result())
            if i % 25 == 0 or i == len(todo):
                done = Counter(x["status"] for x in results)
                print(f"  [{i}/{len(todo)}] {dict(done)}", flush=True)

    out = os.path.join(ROOT, "shared", "paper", "quality", "reference_fetch_report.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"attempted": len(todo), "results": results}, open(out, "w"), indent=1)
    c = Counter(x["status"] for x in results)
    print(f"\nfetched ok : {c.get('ok', 0)}")
    for k, v in sorted(c.items()):
        if k != "ok":
            print(f"  {k}: {v}")
    print(f"report: {out}")
    return 0


if __name__ == "__main__":
    from collections import Counter  # noqa: E402
    sys.exit(main())
