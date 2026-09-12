#!/usr/bin/env python3
"""The compute-matched Solo-versus-Team budget curve, on the scale that means something.

Every published v1 comparison ran the conditions at different compute: Solo 20
LLM turns, Restricted 30, two-role teams 40, Full Team up to 140. Any difference
measured that way is confounded with a 7x budget gap. harness/agent_loop.py's
TurnBudget now gives every condition one shared allowance, and this reads the
resulting sweep.

Two scales are reported because they answer different questions.

  raw           partial_score as the grader emits it, guards included. Across
                the verified core 303 of 374 checks (81%) pass on an untouched
                workspace, so the do-nothing floor is 0.815 and every condition
                is compressed into the top fifth of the range. This is the scale
                the v1 numbers were on.

  discriminative  only the checks that fail on that task's pristine workspace,
                which is the per-(task, check) definition in
                shared/paper/quality/pristine_checks_core.json. Doing nothing
                scores 0 by construction, so the number is the fraction of the
                available signal a condition actually captured.

Guards are not removed, they are moved out of the score: "source still parses"
and "tests not deleted" do real anti-cheat work, and a submission that trips one
is reported as inadmissible rather than merely low-scoring.

Usage:
  python scripts/budget_curve.py
  python scripts/budget_curve.py --dir shared/ablation_results/budget_sweep/core_tasks
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os
import re
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(REPO, "shared", "paper", "quality")


def check_key(c: dict) -> str:
    return str(c.get("id") or "") + "|" + str(c.get("note") or "")[:80]


def load_baseline() -> dict:
    p = os.path.join(Q, "pristine_checks_core.json")
    if not os.path.isfile(p):
        print("missing %s; run scripts/core_pristine_baseline.py first" % p,
              file=sys.stderr)
        sys.exit(2)
    return json.load(open(p))


def checks_for(run: dict) -> list:
    """Per-check results, from the checkpoint if present, else the run dir.

    Older campaigns recorded only the aggregate, so the run directory is the
    fallback. It is a fallback and not the primary source because run dirs live
    on scratch and get cleaned.
    """
    if run.get("checks"):
        return run["checks"]
    rd = run.get("run_dir") or ""
    sp = os.path.join(rd, "reports", "score.json")
    if not os.path.isfile(sp):
        return []
    try:
        sc = json.load(open(sp))
    except Exception:
        return []
    return (sc.get("secondary") or {}).get("checks") or sc.get("checklist") or []


def rescore(checks: list, base: dict):
    """(admissible, discriminative score) for one run."""
    free = set(base["free"])
    guard_ok, passed, n = True, 0, 0
    for c in checks:
        if not isinstance(c, dict):
            continue
        if check_key(c) in free:
            guard_ok &= bool(c.get("ok"))
        else:
            n += 1
            passed += bool(c.get("ok"))
    return guard_ok, (passed / n if n else None)


def wilson(k: int, n: int):
    if not n:
        return (0.0, 0.0)
    z, p = 1.96, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(
        REPO, "shared", "ablation_results", "budget_sweep", "core_tasks"))
    ap.add_argument("--out", default=os.path.join(Q, "budget_curve_core.json"))
    a = ap.parse_args()

    base = load_baseline()
    # budget -> condition -> task -> row
    data: dict = collections.defaultdict(lambda: collections.defaultdict(dict))
    for cp in sorted(glob.glob(os.path.join(a.dir, "*.checkpoint.jsonl"))):
        m = re.search(r"budget(\d+)_", os.path.basename(cp))
        if not m:
            continue
        b = int(m.group(1))
        for line in open(cp):
            try:
                r = json.loads(line)
            except Exception:
                continue
            t, cond = r.get("task_id"), r.get("condition")
            if not t or not cond or t not in base:
                continue
            adm, disc = rescore(checks_for(r), base[t])
            data[b][cond][t] = {
                "raw": r.get("partial_score"), "pass": bool(r.get("pass")),
                "admissible": adm, "disc": disc,
                "turns": r.get("elapsed_sec"),
            }

    if not data:
        print("no runs found under %s" % a.dir, file=sys.stderr)
        return 1

    print("compute-matched budget curve, %d task(s) in the core baseline\n" % len(base))
    hdr = ("budget  condition   n   pass        raw mean   disc mean   inadmissible")
    print(hdr)
    print("-" * len(hdr))
    rows = []
    for b in sorted(data):
        for cond in ("oracle", "full"):
            d = data[b].get(cond) or {}
            if not d:
                continue
            n = len(d)
            k = sum(1 for v in d.values() if v["pass"])
            raw = [v["raw"] for v in d.values() if isinstance(v["raw"], (int, float))]
            disc = [v["disc"] for v in d.values() if isinstance(v["disc"], (int, float))]
            inad = sum(1 for v in d.values() if not v["admissible"])
            lo, hi = wilson(k, n)
            print("%6d  %-10s %3d  %2d/%-2d %4.0f%%  %8.3f   %8.3f   %d" % (
                b, "Solo" if cond == "oracle" else "Full Team", n, k, n,
                100 * k / n, statistics.mean(raw) if raw else float("nan"),
                statistics.mean(disc) if disc else float("nan"), inad))
            rows.append({"budget": b, "condition": cond, "n": n, "passes": k,
                         "pass_rate": k / n, "pass_ci95": [lo, hi],
                         "raw_mean": statistics.mean(raw) if raw else None,
                         "disc_mean": statistics.mean(disc) if disc else None,
                         "inadmissible": inad})

    # paired within-task comparison at each budget, which is the actual question
    print("\npaired Solo vs Full Team, same task, same budget:")
    for b in sorted(data):
        o, f = data[b].get("oracle") or {}, data[b].get("full") or {}
        common = sorted(set(o) & set(f))
        if not common:
            continue
        both = [(o[t], f[t]) for t in common]
        dd = [y["disc"] - x["disc"] for x, y in both
              if isinstance(x["disc"], (int, float)) and isinstance(y["disc"], (int, float))]
        team_only = sum(1 for x, y in both if y["pass"] and not x["pass"])
        solo_only = sum(1 for x, y in both if x["pass"] and not y["pass"])
        line = "  budget %3d  n=%2d  team-only wins %d, solo-only wins %d" % (
            b, len(common), team_only, solo_only)
        if dd:
            line += "  mean disc delta %+.3f" % statistics.mean(dd)
        print(line)

    # A sign test on the paired outcomes. The question is not whether the team
    # mean is lower but whether the team ever wins a task the solo agent loses,
    # at the same budget on the same task.
    tw = sw = 0
    for b in data:
        o, f = data[b].get("oracle") or {}, data[b].get("full") or {}
        for t in set(o) & set(f):
            if f[t]["pass"] and not o[t]["pass"]:
                tw += 1
            elif o[t]["pass"] and not f[t]["pass"]:
                sw += 1
    n = tw + sw
    if n:
        # two-sided exact binomial against p=0.5
        pv = min(1.0, 2 * sum(math.comb(n, k) for k in range(0, min(tw, sw) + 1)) / 2 ** n)
        print("\ndiscordant task-budget pairs: %d  (team-only %d, solo-only %d)" % (n, tw, sw))
        print("  exact two-sided sign test p = %.2g" % pv)
    else:
        pv = None
        print("\nno discordant pairs")

    json.dump({"rows": rows, "sign_test": {"team_only": tw, "solo_only": sw,
                                           "n_discordant": n, "p_two_sided": pv},
               "per_task": {str(b): {c: data[b][c] for c in data[b]} for b in data}},
              open(a.out, "w"), indent=1)
    print("\nwrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
