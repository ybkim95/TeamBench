#!/usr/bin/env python3
"""Verifier abstention: how often the control never reaches a conclusion.

The paper treats runs without an attestation as "missing" and drops them from the
false-accept denominator (981 of 2,025 in the role-mixing grid). That framing
assumes the absence is a measurement gap. It is not. A verification role that
inspects an artifact and then files no verdict has failed in a distinct and
reportable way: the control produced no decision at all. Under a separation-of-
duties reading that is worse than a wrong verdict, because nothing downstream can
act on it.

This script separates four causes that the single "missing" label conflates:

  ABSTAINED        no attestation anywhere, and the verifier used its whole turn
                   budget. It inspected and never concluded.
  QUIT_EARLY       no attestation anywhere, but the verifier stopped before the
                   budget was spent. It ended without concluding.
  MISPLACED        an attestation exists, but outside submission/, so the harness
                   scored it as missing. This one IS a measurement artifact.
  MALFORMED        an attestation exists in the right place but no pass/fail
                   verdict can be parsed from it.

and reports what the false-accept rate becomes under each treatment of the
abstentions, since that choice moves the headline number.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERDICT_RE = re.compile(r'"verdict"\s*:\s*"(pass|fail)"')


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def find_attestations(run_dir):
    """Every attestation on disk, with the canonical one first."""
    hits = []
    for sub in ("submission", "workspace", "reports"):
        base = os.path.join(run_dir, sub)
        if not os.path.isdir(base):
            continue
        for dirpath, _, files in os.walk(base):
            for fn in files:
                if fn == "attestation.json":
                    hits.append(os.path.join(dirpath, fn))
    canon = os.path.join(run_dir, "submission", "attestation.json")
    hits.sort(key=lambda p: (p != canon, len(p)))
    return hits, canon


def verifier_turns(run_dir):
    """(turns_used, budget_hint) from the last verifier attempt's logs."""
    vdir = os.path.join(run_dir, "logs", "verifier")
    attempts = sorted(glob.glob(os.path.join(vdir, "attempt_*")),
                      key=lambda p: int(p.rsplit("_", 1)[-1])) or [vdir]
    last = attempts[-1]
    turns = sorted(glob.glob(os.path.join(last, "turn_*.json")))
    return len(turns), last


def classify(run_dir, budget=20):
    hits, canon = find_attestations(run_dir)
    n_turns, _ = verifier_turns(run_dir)
    if not os.path.isdir(os.path.join(run_dir, "logs", "verifier")):
        return None                      # not a run with a verifier phase

    for p in hits:
        raw = open(p, encoding="utf-8", errors="replace").read()
        try:
            v = (json.loads(raw) or {}).get("verdict")
        except Exception:
            m = VERDICT_RE.search(raw)
            v = m.group(1) if m else None
        if v in ("pass", "fail"):
            return {"outcome": "VERDICT" if p == canon else "MISPLACED",
                    "verdict": v, "path": os.path.relpath(p, run_dir),
                    "turns": n_turns}
    if hits:
        return {"outcome": "MALFORMED", "verdict": None,
                "path": os.path.relpath(hits[0], run_dir), "turns": n_turns}
    return {"outcome": "ABSTAINED" if n_turns >= budget else "QUIT_EARLY",
            "verdict": None, "path": None, "turns": n_turns}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+",
                    default=["shared/role_ablation/runs", "shared/ablation_runs",
                             "shared/gemma4_26b_api_campaign/runs"])
    ap.add_argument("--budget", type=int, default=20)
    ap.add_argument("--out", default="shared/paper/quality/verifier_abstention.json")
    a = ap.parse_args()

    # Run directories sit at different depths across campaigns:
    #   shared/ablation_runs/<task>/<ts>/
    #   shared/role_ablation/runs/<config>/<task>/<ts>/
    # so search a depth range rather than assuming one layout.
    runs = []
    for root in a.roots:
        r = os.path.join(REPO, root)
        for depth in range(1, 5):
            pat = os.path.join(r, *(["*"] * depth), "logs", "verifier")
            for vdir in glob.glob(pat):
                runs.append(os.path.dirname(os.path.dirname(vdir)))
    runs = sorted(set(runs))
    print(f"runs with a verifier phase: {len(runs)}", flush=True)

    # grader outcome per run, keyed by run_dir, from the role-mixing ledger
    grader = {}
    led = os.path.join(REPO, "shared/role_ablation/results/per_run.jsonl")
    if os.path.isfile(led):
        for line in open(led):
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("run_dir"):
                rd = os.path.normpath(d["run_dir"])
                grader[rd] = bool(d.get("pass"))
                grader[os.path.abspath(rd)] = bool(d.get("pass"))

    rows = []
    for i, rd in enumerate(runs, 1):
        c = classify(rd, a.budget)
        if c:
            c["run_dir"] = rd
            c["grader_pass"] = grader.get(os.path.normpath(rd),
                                      grader.get(os.path.abspath(rd)))
            rows.append(c)
        if i % 300 == 0:
            print(f"  {i}/{len(runs)}", flush=True)

    os.makedirs(os.path.dirname(os.path.join(REPO, a.out)), exist_ok=True)
    json.dump(rows, open(os.path.join(REPO, a.out), "w"), indent=1)

    n = len(rows)
    c = collections.Counter(r["outcome"] for r in rows)
    print(f"\nVERIFIER OUTCOME, n={n}")
    for k in ("VERDICT", "MISPLACED", "MALFORMED", "ABSTAINED", "QUIT_EARLY"):
        v = c.get(k, 0)
        print(f"  {k:11} {v:5}  {100*v/max(1,n):5.1f}%")
    noconc = c.get("ABSTAINED", 0) + c.get("QUIT_EARLY", 0) + c.get("MALFORMED", 0)
    print(f"  {'-'*30}\n  no usable verdict: {noconc} = {100*noconc/max(1,n):.1f}%")
    print(f"  of which recoverable by fixing the read path (MISPLACED): {c.get('MISPLACED',0)}")

    # what the false-accept rate becomes under each treatment
    known = [r for r in rows if r["grader_pass"] is False]
    withv = [r for r in known if r["verdict"] in ("pass", "fail")]
    fa = [r for r in withv if r["verdict"] == "pass"]
    absts = [r for r in known if r["verdict"] is None]
    print(f"\nFALSE-ACCEPT on grader-failing runs (n_grader_fail={len(known)})")
    for lbl, k, d in (
        ("abstentions excluded (as published)", len(fa), len(withv)),
        ("abstentions counted as accept", len(fa) + len(absts), len(known)),
        ("abstentions counted as reject", len(fa), len(known)),
    ):
        lo, hi = wilson(k, d) if d else (0, 0)
        print(f"  {lbl:36} {k:4}/{d:<4} = {100*k/max(1,d):5.1f}%  [{100*lo:.0f}%, {100*hi:.0f}%]")
    print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
