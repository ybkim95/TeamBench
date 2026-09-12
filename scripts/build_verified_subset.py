#!/usr/bin/env python3
"""Build the TeamBench-Verified subset (SWE-Bench-Verified analog).

Eligibility for inclusion in TeamBench-Verified:
  1. Task is a member of TeamBench-100 (LB100).
  2. canonical_pass_check.json result is one of:
       canonical_in_workspace | canonical_via_llm_run | canonical_via_pr
     (i.e. NOT canonical_unknown).
  3. mutation_kill.json kill_rate >= MUT_THRESHOLD (default 0.5) OR
     the task has no Python files to mutate (in which case we accept
     based on the canonical-check result alone).
  4. discrimination_score >= DISCRIM_THRESHOLD (default 0.10) — at least
     two LB100 models with different outcomes on this task.
  5. validate_task_quality.py Gate 1 (structural) is informational; we
     do NOT use it as a hard filter because for tasks where the seed-0
     workspace is intentionally the buggy state, G1 reports "grader
     crashed on generated workspace" with the workspace's expected-buggy
     failure modes — that's correct behavior, not a structural defect.
     Tasks where G1 truly fails AND canonical-check is unknown are
     reviewed manually.

Produces:
  shared/paper/teambench_verified.json
  shared/paper/teambench_verified_summary.md

Each task entry includes the per-criterion outcome plus links to the source
artifacts so reviewers can audit the eligibility decision per task.

Usage:
  python scripts/build_verified_subset.py
  python scripts/build_verified_subset.py --mut-threshold 0.7 --discrim-threshold 0.2
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QDIR = os.path.join(REPO, "shared/paper/teambench_quality")
OUT_JSON = os.path.join(REPO, "shared/paper/teambench_verified.json")
OUT_MD = os.path.join(REPO, "shared/paper/teambench_verified_summary.md")
LB100 = os.path.join(REPO, "leaderboard/data/leaderboard_100_tasks.json")
VAL_DIR = os.path.join(REPO, "shared/validation_reports")


def _load(path):
    if not os.path.isfile(path):
        return None
    return json.load(open(path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mut-threshold", type=float, default=0.5)
    ap.add_argument("--discrim-threshold", type=float, default=0.10)
    args = ap.parse_args()

    # Tasks whose grader scores a deliverable artefact (e.g. config.json)
    # rather than running the workspace source code. Mutating workspace
    # python files cannot affect the grader's verdict by design, so we
    # exempt these tasks from the mutation-kill criterion. Each exemption
    # must be justified in repair_changelog.md.
    MUTATION_EXEMPT = {
        "O6_perf_tuning": "grader scores config.json output via simulator.py; mutating optimizer.py / simulator.py is by-design irrelevant",
    }

    canon = _load(os.path.join(QDIR, "canonical_pass_check.json"))
    if not canon:
        raise SystemExit("missing canonical_pass_check.json — run check_canonical_solution.py first")
    canon_by = {r["task_id"]: r for r in canon["results"]}

    mut = _load(os.path.join(QDIR, "mutation_kill.json"))
    mut_by = {r["task_id"]: r for r in (mut or {}).get("results", [])}

    discrim = _load(os.path.join(QDIR, "task_discrimination.json"))
    discrim_by = (discrim or {}).get("tasks", {})

    lb = _load(LB100)
    lb100_ids = [t["task_id"] if isinstance(t, dict) else t for t in lb["tasks"]]

    rows = []
    for tid in lb100_ids:
        cr = canon_by.get(tid, {"result": "no_check_run"})
        mr = mut_by.get(tid, {})
        dr = discrim_by.get(tid, {})

        # Validation gate 1
        val_path = os.path.join(VAL_DIR, f"{tid}.json")
        g1 = None
        if os.path.isfile(val_path):
            try:
                v = json.load(open(val_path))
                g1_status = next((g["status"] for g in v.get("gates", []) if g["name"] == "gate1_structural"), None)
                g1 = (g1_status == "PASS")
            except Exception:
                g1 = None

        canon_ok = cr.get("result") in ("canonical_in_workspace", "canonical_via_llm_run", "canonical_via_pr")
        kill_rate = mr.get("kill_rate")
        # Mutation: pass if kill_rate >= threshold; if mutation test wasn't applicable
        # (e.g. no python files OR base workspace didn't pass), accept based on canonical alone
        if tid in MUTATION_EXEMPT:
            mut_ok = True
            mut_reason = f"exempt: {MUTATION_EXEMPT[tid]}"
        elif kill_rate is None:
            mut_ok = True if canon_ok else False
            mut_reason = mr.get("notes", "no mutation result")
        else:
            mut_ok = kill_rate >= args.mut_threshold
            mut_reason = f"kill_rate={kill_rate}"

        discrim_score = dr.get("discrimination_score")
        discrim_ok = (discrim_score is not None) and (discrim_score >= args.discrim_threshold)

        eligible = canon_ok and mut_ok and discrim_ok

        rows.append({
            "task_id": tid,
            "eligible": eligible,
            "criteria": {
                "g1_structural": g1,
                "canonical_solution": cr.get("result"),
                "mutation_kill_rate": kill_rate,
                "mutation_passes": mut_ok,
                "mutation_reason": mut_reason,
                "discrimination_score": discrim_score,
                "discrimination_passes": discrim_ok,
            },
        })

    eligible_ids = [r["task_id"] for r in rows if r["eligible"]]

    # Layer triage buckets (from unknown_triage.json) into each row
    triage = _load(os.path.join(QDIR, "unknown_triage.json"))
    triage_by = {r["task_id"]: r for r in (triage or {}).get("rows", [])}
    for r in rows:
        t = triage_by.get(r["task_id"])
        if t:
            r["triage_bucket"] = t["bucket"]
            r["best_historical_partial"] = t["best_partial"]
        else:
            r["triage_bucket"] = "verified" if r["eligible"] else "needs_review"

    triage_counts = {}
    for r in rows:
        b = r["triage_bucket"]
        triage_counts[b] = triage_counts.get(b, 0) + 1

    summary = {
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "thresholds": {
            "mutation_kill_rate_min": args.mut_threshold,
            "discrimination_score_min": args.discrim_threshold,
            "g1_structural_required": False,
            "canonical_solution_required": True,
        },
        "lb100_total": len(lb100_ids),
        "verified_total": len(eligible_ids),
        "verified_task_ids": eligible_ids,
        "triage_bucket_counts": triage_counts,
        "drop_reasons_count": {},
        "rows": rows,
    }
    drop_reasons = {}
    for r in rows:
        if r["eligible"]:
            continue
        c = r["criteria"]
        bucket = []
        if not c["g1_structural"]:                 bucket.append("g1_structural")
        if c["canonical_solution"] not in ("canonical_in_workspace", "canonical_via_llm_run", "canonical_via_pr"):
            bucket.append(f"canonical={c['canonical_solution']}")
        if not c["mutation_passes"]:               bucket.append("mutation_kill_rate")
        if not c["discrimination_passes"]:         bucket.append("discrimination_score")
        key = "+".join(bucket) if bucket else "unknown"
        drop_reasons[key] = drop_reasons.get(key, 0) + 1
    summary["drop_reasons_count"] = drop_reasons

    json.dump(summary, open(OUT_JSON, "w"), indent=2)
    print(f"[verified] wrote {OUT_JSON}")
    print(f"[verified] eligible: {len(eligible_ids)} of {len(lb100_ids)}")
    for k, n in sorted(drop_reasons.items(), key=lambda kv: -kv[1]):
        print(f"  drop because {k}: {n}")

    # Markdown summary
    md = [
        "# TeamBench-Verified",
        "",
        f"_Computed {summary['computed_at']}._",
        f"_Eligibility: canonical solution verified AND mutation_kill_rate ≥ {args.mut_threshold} AND discrimination_score ≥ {args.discrim_threshold}._",
        "",
        f"**{len(eligible_ids)} of {len(lb100_ids)} LB100 tasks qualify (TeamBench-Verified).**",
        "",
        "## Triage buckets across the full LB100",
        "",
        "| Bucket | Count | Meaning |",
        "|---|---|---|",
        f"| verified | {triage_counts.get('verified',0)} | passes all checks → in TeamBench-Verified |",
        f"| near_miss_very_close | {triage_counts.get('near_miss_very_close',0)} | best historical partial ≥ 0.9; grader has 1-2 over-strict checks |",
        f"| near_miss | {triage_counts.get('near_miss',0)} | best historical partial 0.7-0.9; solvable but harder |",
        f"| solvable_in_principle | {triage_counts.get('solvable_in_principle',0)} | best historical partial 0.4-0.7; partial credit but not converging |",
        f"| broken_grader_post_pr | {triage_counts.get('broken_grader_post_pr',0)} | static workspace IS post-PR canonical fix but grader needs runtime deps (compiled numpy/scipy/etc) — recommend remove from LB100 |",
        f"| no_progress | {triage_counts.get('no_progress',0)} | best partial < 0.3; needs manual review |",
        "",
        "## Drop reasons (Verified eligibility)",
        "",
        "| Reason | Count |",
        "|---|---|",
    ]
    for k, n in sorted(drop_reasons.items(), key=lambda kv: -kv[1]):
        md.append(f"| {k} | {n} |")
    md.extend([
        "",
        "## Verified task ids",
        "",
        "```",
        *eligible_ids,
        "```",
    ])
    open(OUT_MD, "w").write("\n".join(md) + "\n")
    print(f"[verified] wrote {OUT_MD}")
    print(f"[verified] triage buckets: {triage_counts}")


if __name__ == "__main__":
    main()
