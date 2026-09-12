#!/usr/bin/env python3
"""Triage canonical_unknown LB100 tasks: which are near-misses vs broken?

For each task that ended up canonical_unknown:
  - Find the highest historical partial_score across all (model, condition) runs.
  - Count runs at partial >= 0.5 / 0.7 / 0.9.
  - For GH-sourced tasks, check whether the static workspace is the post-PR
    canonical state (patch --dry-run --forward returns "Reversed (or
    previously applied)").

Output:
  shared/paper/teambench_quality/unknown_triage.json

Buckets:
  - "near_miss"        : best partial >= 0.7 — task is solvable, grader needs slight relaxation or harder tries
  - "solvable_in_principle" : best partial in [0.4, 0.7) — partial credit but not full
  - "broken_grader_post_pr" : GH-sourced AND static workspace is post-PR but no run passes — grader needs runtime deps
  - "no_progress"      : best partial < 0.4 across all runs — likely too hard or genuinely broken
"""
from __future__ import annotations

import json, os, re, subprocess, tempfile, shutil
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QDIR = os.path.join(REPO, "shared/paper/teambench_quality")
OUT = os.path.join(QDIR, "unknown_triage.json")
ABL = os.path.join(REPO, "shared/ablation_results")
TASKS = os.path.join(REPO, "tasks")
PR_DIFFS = os.path.join(QDIR, "pr_diffs")


def harvest_partial_scores():
    by_task = defaultdict(list)
    for fn in sorted(os.listdir(ABL)):
        if not fn.startswith("lb100_") or any(s in fn for s in ("invalid", "archived", "pre_", ".bak")):
            continue
        path = os.path.join(ABL, fn)
        if not os.path.isfile(path): continue
        records = []
        if fn.endswith(".json"):
            try: d = json.load(open(path))
            except: continue
            records = d.get("runs", []) if isinstance(d, dict) else (d if isinstance(d, list) else [])
        elif fn.endswith(".checkpoint.jsonl"):
            for line in open(path):
                try: records.append(json.loads(line))
                except: continue
        for r in records:
            if not isinstance(r, dict): continue
            tid = r.get("task_id") or r.get("task")
            if tid:
                by_task[tid].append({
                    "condition": r.get("condition"),
                    "partial_score": r.get("partial_score") if r.get("partial_score") is not None else (1.0 if r.get("pass") else 0.0),
                    "pass": bool(r.get("pass") or r.get("passed")),
                })
    return by_task


def check_static_post_pr(task_id):
    """Return True if the static tasks/<id>/workspace is at the post-PR state."""
    pr_url_re = re.compile(r"https://github\.com/([\w.-]+)/([\w.-]+)/pull/(\d+)")
    gen_path = os.path.join(REPO, "generators", f"gen_{task_id.lower()}.py")
    if not os.path.isfile(gen_path):
        for fn in os.listdir(os.path.join(REPO, "generators")):
            if fn.lower() == f"gen_{task_id.lower()}.py":
                gen_path = os.path.join(REPO, "generators", fn); break
        else: return None
    head = open(gen_path).read(3000)
    m = pr_url_re.search(head)
    if not m: return None
    org, repo, num = m.group(1), m.group(2), m.group(3)
    cache = os.path.join(PR_DIFFS, f"{org}_{repo}_pr{num}.diff")
    if not os.path.isfile(cache): return None
    static_ws = os.path.join(TASKS, task_id, "workspace")
    if not os.path.isdir(static_ws): return None
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(static_ws, os.path.join(tmp, "ws"))
        p = subprocess.run(
            ["patch", "-p1", "--dry-run", "--forward"],
            input=open(cache).read(), text=True, capture_output=True,
            cwd=os.path.join(tmp, "ws"), timeout=30,
        )
        return "Reversed (or previously applied)" in (p.stdout + p.stderr)


def main():
    canon = json.load(open(os.path.join(QDIR, "canonical_pass_check.json")))
    unknown = [r["task_id"] for r in canon["results"] if r["result"] == "canonical_unknown"]
    print(f"[triage] {len(unknown)} canonical_unknown tasks")
    ps = harvest_partial_scores()
    rows = []
    bucket_counts = defaultdict(int)
    for tid in unknown:
        runs = ps.get(tid, [])
        scores = [r["partial_score"] for r in runs if r["partial_score"] is not None]
        best = max(scores) if scores else 0.0
        n_high = sum(1 for s in scores if s >= 0.7)
        n_mid = sum(1 for s in scores if s >= 0.5)
        n_low = sum(1 for s in scores if s >= 0.3)
        post_pr = check_static_post_pr(tid)

        if post_pr is True:
            bucket = "broken_grader_post_pr"
        elif best >= 0.9:
            bucket = "near_miss_very_close"
        elif best >= 0.7:
            bucket = "near_miss"
        elif best >= 0.4:
            bucket = "solvable_in_principle"
        elif best > 0:
            bucket = "low_progress"
        else:
            bucket = "no_progress"
        bucket_counts[bucket] += 1

        rows.append({
            "task_id": tid,
            "n_runs": len(runs),
            "best_partial": round(best, 3),
            "n_runs_partial_ge_0.7": n_high,
            "n_runs_partial_ge_0.5": n_mid,
            "n_runs_partial_ge_0.3": n_low,
            "static_workspace_is_post_pr": post_pr,
            "bucket": bucket,
        })

    rows.sort(key=lambda r: (-r["best_partial"], r["task_id"]))

    out = {
        "n_unknown": len(unknown),
        "bucket_counts": dict(bucket_counts),
        "rows": rows,
    }
    json.dump(out, open(OUT, "w"), indent=2)
    print(f"[triage] wrote {OUT}")
    print(f"[triage] bucket counts: {dict(bucket_counts)}")
    print()
    print("Top near-misses (best_partial >= 0.7):")
    for r in rows:
        if r["best_partial"] >= 0.7:
            print(f"  {r['task_id']:<40} best={r['best_partial']:.3f}  n_runs={r['n_runs']:>3}  n_high={r['n_runs_partial_ge_0.7']:>2}  bucket={r['bucket']}")


if __name__ == "__main__":
    main()
