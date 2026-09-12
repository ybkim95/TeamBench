#!/usr/bin/env python3
"""
Read the G3 reference ledger (or its live checkpoint) and print the numbers the
paper needs, with Wilson intervals on every proportion.

    python3 scripts/g3_analysis.py [--checkpoint] [--out shared/paper/quality/g3_headline.json]

Definitions, restated so no reader has to reconstruct them:

  (a) a_validated                 reference applies AND grader gives 1.0
  (b) b_grader_rejects_reference  reference applies AND grader gives < 1.0
  (c) c_unappliable               reference cannot be applied by any method

Within (b) the sub-populations that matter:

  reference == pristine floor   the grader awards the upstream fix exactly what
                                it awards an empty workspace: it is blind to the
                                fix.
  reference <  pristine floor   applying the upstream fix LOSES points.
  dead checks                   checks that fail on the pristine workspace AND
                                on the reference. No solution can pass them, so
                                they cap every task's attainable score.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter, defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUALITY = os.path.join(REPO_ROOT, "shared", "paper", "quality")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, c - h), 4), round(min(1.0, c + h), 4))


def load(use_checkpoint: bool) -> tuple[list[dict], dict]:
    ledger = os.path.join(QUALITY, "g3_reference_ledger.json")
    ckpt = os.path.join(QUALITY, "g3_reference_checkpoint.jsonl")
    if not use_checkpoint and os.path.isfile(ledger):
        d = json.load(open(ledger, encoding="utf-8"))
        return d["tasks"], d["summary"].get("meta", {})
    recs, seen = [], set()
    with open(ckpt, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r["task_id"] in seen:
                continue
            seen.add(r["task_id"])
            recs.append(r)
    recs.sort(key=lambda r: r["task_id"])
    return recs, {"source": "checkpoint (run in progress)"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", action="store_true")
    ap.add_argument("--out", default=os.path.join(QUALITY, "g3_headline.json"))
    args = ap.parse_args()
    recs, meta = load(args.checkpoint)
    # A grade that hit the 300 s harness cap says nothing about whether the
    # grader accepts the upstream fix. Reclassify before counting.
    for r in recs:
        ref = r.get("reference") or {}
        pri = r.get("pristine") or {}
        if r.get("outcome") in ("a_validated", "b_grader_rejects_reference") and (
                ref.get("timed_out") or pri.get("timed_out")
                or ref.get("partial_score") is None):
            r["outcome"] = "d_inconclusive_grader_timeout"
    n = len(recs)
    oc = Counter(r.get("outcome", "error") for r in recs)

    print(f"N = {n} tasks with tasks/<id>/reference/patch.diff, graded at seed 0")
    print()
    print(f"{'outcome':32s} {'n':>5s} {'share':>8s}  95% Wilson")
    for k in ("a_validated", "b_grader_rejects_reference", "c_unappliable",
              "d_inconclusive_grader_timeout", "error"):
        v = oc.get(k, 0)
        lo, hi = wilson(v, n)
        print(f"{k:32s} {v:5d} {v/n:8.1%}  [{lo:.3f}, {hi:.3f}]")
    print()

    applied = [r for r in recs if r.get("outcome", "").startswith(("a_", "b_"))]
    b = [r for r in recs if r.get("outcome") == "b_grader_rejects_reference"]
    a = [r for r in recs if r.get("outcome") == "a_validated"]
    if applied:
        lo, hi = wilson(len(a), len(applied))
        print(f"Among the {len(applied)} tasks whose reference APPLIED, "
              f"{len(a)} score 1.0 ({len(a)/len(applied):.1%}, Wilson [{lo:.3f}, {hi:.3f}])")
    print()

    eq = [r for r in b if r.get("reference_minus_floor") == 0.0]
    neg = [r for r in b if (r.get("reference_minus_floor") or 0) < 0]
    pos = [r for r in b if (r.get("reference_minus_floor") or 0) > 0]
    print("Bucket (b) decomposition")
    print(f"  reference == pristine floor (grader blind to the fix) : {len(eq)} "
          f"({len(eq)/len(b):.1%} of b)" if b else "  (empty)")
    if b:
        print(f"  reference <  pristine floor (fix loses points)        : {len(neg)}")
        print(f"  reference >  pristine floor but still < 1.0          : {len(pos)}")
        scores = [(r.get("reference") or {}).get("partial_score") for r in b]
        scores = [s for s in scores if s is not None]
        if scores:
            scores_sorted = sorted(scores)
            print(f"  reference partial score: mean {sum(scores)/len(scores):.3f}, "
                  f"median {scores_sorted[len(scores)//2]:.3f}, "
                  f"min {min(scores):.3f}, max {max(scores):.3f}")
        floors = [(r.get("pristine") or {}).get("partial_score") for r in b]
        floors = [f for f in floors if f is not None]
        if floors:
            print(f"  pristine floor on the same tasks: mean {sum(floors)/len(floors):.3f}")
    print()

    # Dead checks: fail pristine AND fail with the reference applied.
    dead_counter = Counter()
    dead_per_task = []
    flipped = Counter()
    for r in b:
        ref = r.get("reference") or {}
        failed = set(ref.get("checks_failed_ids") or [])
        broke = set(r.get("checks_flipped_to_fail") or [])
        dead = failed - broke
        dead_per_task.append(len(dead))
        for c in dead:
            dead_counter[c] += 1
        for c in broke:
            flipped[c] += 1
    have = [r for r in b if r.get("checks_flipped_to_pass") is not None]
    zero_disc = [r for r in have if len(r["checks_flipped_to_pass"]) == 0]
    if have:
        print(f"Tasks where NOT ONE check flips fail->pass when the upstream fix is "
              f"applied: {len(zero_disc)}/{len(have)} ({len(zero_disc)/len(have):.1%})")
        print("  distribution of checks flipped:",
              sorted(Counter(len(r["checks_flipped_to_pass"]) for r in have).items()))
        broke_n = sum(1 for r in have if r.get("checks_flipped_to_fail"))
        print(f"  tasks where the upstream fix breaks a previously passing check: {broke_n}")
        free = [len(r.get("checks_free") or []) for r in have]
        tots = [(r.get("reference") or {}).get("checks_total") for r in have]
        tots = [t for t in tots if t]
        if free and tots:
            print(f"  mean checks already passing on the pristine workspace: "
                  f"{sum(free)/len(free):.2f} of {sum(tots)/len(tots):.2f}")
        print()

    if dead_per_task:
        print(f"Dead checks (fail pristine AND fail with the upstream fix applied): "
              f"{sum(dead_per_task)} across {len(b)} bucket-(b) tasks, "
              f"mean {sum(dead_per_task)/len(dead_per_task):.2f} per task")
        print("  most common:", dead_counter.most_common(8))
    if flipped:
        print("Checks the upstream fix BREAKS (pass pristine, fail with the fix):",
              flipped.most_common(8))
    print()

    meth = Counter((r.get("application") or {}).get("method") for r in recs)
    print("Apply method:", meth.most_common())
    ht = sum((r.get("application") or {}).get("hunks_total") or 0 for r in recs)
    ha = sum((r.get("application") or {}).get("hunks_applied") or 0 for r in recs)
    hl = sum((r.get("application") or {}).get("hunks_already") or 0 for r in recs)
    hf = sum((r.get("application") or {}).get("hunks_failed") or 0 for r in recs)
    print(f"Hunks: total {ht}, applied {ha}, already at post state {hl}, failed {hf}"
          + (f"  -> {(ha+hl)/ht:.2%} reached the post state" if ht else ""))
    noeff = sum(1 for r in recs if (r.get("application") or {}).get("no_effective_change"))
    print(f"Applied but no effective change in the workspace: {noeff}")
    timeouts = sum(1 for r in recs
                   if (r.get("reference") or {}).get("timed_out")
                   or (r.get("pristine") or {}).get("timed_out"))
    print(f"Grader timeouts (either grade): {timeouts}")

    fam = defaultdict(Counter)
    for r in recs:
        fam[r.get("family", "?")][r.get("outcome", "error")] += 1
    print()
    print("By family:", {k: dict(v) for k, v in sorted(fam.items())})

    out = {
        "n": n,
        "outcomes": dict(oc),
        "outcome_wilson": {k: wilson(oc.get(k, 0), n) for k in oc},
        "applied_n": len(applied),
        "validated_among_applied": len(a),
        "validated_among_applied_wilson": wilson(len(a), len(applied)) if applied else None,
        "b_reference_equals_floor": len(eq),
        "b_reference_below_floor": len(neg),
        "b_reference_above_floor_below_one": len(pos),
        "tasks_with_per_check_data": len(have),
        "tasks_with_zero_discriminative_checks": len(zero_disc),
        "checks_flipped_distribution": dict(Counter(
            len(r["checks_flipped_to_pass"]) for r in have)),
        "dead_checks_total": sum(dead_per_task),
        "dead_checks_most_common": dead_counter.most_common(15),
        "checks_broken_by_reference": flipped.most_common(15),
        "hunks": {"total": ht, "applied": ha, "already": hl, "failed": hf},
        "apply_methods": dict(meth),
        "no_effective_change": noeff,
        "grader_timeouts": timeouts,
        "by_family": {k: dict(v) for k, v in sorted(fam.items())},
        "source_meta": meta,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("\nwrote", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
