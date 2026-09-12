#!/usr/bin/env python3
"""Inter-coder agreement for the Verifier decision codebook.

Reads two coded CSVs produced from human_eval/coding/decisions_to_code.csv and
reports raw agreement and Cohen's kappa on the FIRST pass, before any
disagreement resolution. Also prints the disagreement list so the two coders can
adjudicate, and a per-code breakdown so a code that nobody agrees on is visible
rather than buried in a single summary number.

Usage:
  python scripts/coding_agreement.py \
      --coder1 human_eval/coding/coding_coder1.csv \
      --coder2 human_eval/coding/coding_coder2.csv

Report kappa on the merged 24 decisions, and also on the two sub-populations
(human pass, human fail) separately, because the C and R code families are
disjoint and a pooled kappa is inflated by that structure alone.
"""
from __future__ import annotations

import argparse
import collections
import csv
import sys


def load(path):
    out = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            uid = row.get("decision_uid")
            code = (row.get("code") or "").strip().upper()
            if uid and code:
                out[uid] = {"code": code, "verdict": row.get("verdict_human"),
                            "note": row.get("note", "")}
    return out


def kappa(pairs):
    """Cohen's kappa for two raters over a shared label set."""
    if not pairs:
        return float("nan"), 0.0, 0.0
    n = len(pairs)
    agree = sum(1 for a, b in pairs if a == b) / n
    labels = {l for p in pairs for l in p}
    m1 = collections.Counter(a for a, _ in pairs)
    m2 = collections.Counter(b for _, b in pairs)
    pe = sum((m1[l] / n) * (m2[l] / n) for l in labels)
    k = (agree - pe) / (1 - pe) if pe < 1 else float("nan")
    return k, agree, pe


def report(label, pairs):
    k, agree, pe = kappa(pairs)
    interp = ("almost perfect" if k >= .81 else "substantial" if k >= .61 else
              "moderate" if k >= .41 else "fair" if k >= .21 else
              "slight" if k >= 0 else "worse than chance")
    print(f"  {label:28} n={len(pairs):3}  raw agreement {agree:5.1%}  "
          f"kappa {k:+.3f}  ({interp})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coder1", default="human_eval/coding/coding_coder1.csv")
    ap.add_argument("--coder2", default="human_eval/coding/coding_coder2.csv")
    a = ap.parse_args()

    try:
        c1, c2 = load(a.coder1), load(a.coder2)
    except FileNotFoundError as e:
        print(f"missing file: {e.filename}", file=sys.stderr)
        print("Coder 2 should fill the 'code' column of "
              "human_eval/coding/decisions_to_code.csv and save it as "
              "human_eval/coding/coding_coder2.csv", file=sys.stderr)
        return 2

    shared = sorted(set(c1) & set(c2))
    only1, only2 = set(c1) - set(c2), set(c2) - set(c1)
    print(f"coded by both: {len(shared)}   only coder1: {len(only1)}   only coder2: {len(only2)}\n")
    if not shared:
        print("nothing to compare")
        return 1

    print("AGREEMENT")
    report("all decisions", [(c1[u]["code"], c2[u]["code"]) for u in shared])
    for v, lbl in (("pass", "human pass (C codes)"), ("fail", "human fail (R codes)")):
        sub = [u for u in shared if c1[u]["verdict"] == v]
        if sub:
            report(lbl, [(c1[u]["code"], c2[u]["code"]) for u in sub])

    dis = [u for u in shared if c1[u]["code"] != c2[u]["code"]]
    print(f"\nDISAGREEMENTS ({len(dis)})")
    for u in dis:
        print(f"  {u}")
        print(f"    coder1={c1[u]['code']}  coder2={c2[u]['code']}")
        print(f"    note: {c1[u]['note'][:100]}")

    print("\nPER-CODE (coder1 label -> what coder2 called it)")
    conf = collections.defaultdict(collections.Counter)
    for u in shared:
        conf[c1[u]["code"]][c2[u]["code"]] += 1
    for k in sorted(conf):
        tot = sum(conf[k].values())
        same = conf[k][k]
        print(f"  {k}: n={tot}, agreed {same} -> {dict(conf[k])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
