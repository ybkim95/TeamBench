#!/usr/bin/env python3
"""Per-provider Verifier rates, recomputed with abstention made explicit.

The submitted paper ranks Verifier providers by false-accept rate on grader-
failing runs, conditioned on a parseable verdict existing:

    GPT-5.4 Mini 36.3%, Haiku 4.5 60.1%, Gemini-3 Flash 77.0%

That denominator drops every run where the Verifier filed no verdict, and the
abstention rate is itself strongly provider-dependent (measured: 12.6% / 41.1% /
73.5%). Conditioning on a variable that differs six-fold across the arms being
compared is a selection effect, so the ranking cannot be read off the conditional
rate alone.

This recomputes each provider on all three denominators from the raw run ledger
plus the on-disk attestations, so the paper can report the rate together with the
selection it is conditioned on:

  conditional     accepts / (runs with a verdict, grader-failing)   [as published]
  abstain=accept  accepts + abstentions / all grader-failing runs   [upper bound]
  abstain=reject  accepts / all grader-failing runs                 [lower bound]

The Verifier provider is the third role in the config code (P?E?V?), i.e. the
letter at index 5 of e.g. "PGEAVO".
"""
from __future__ import annotations

import collections
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(REPO, "shared", "paper", "quality")
PROV = {"A": "Anthropic (Haiku-4.5)", "G": "Google (Gemini-3 Flash)",
        "O": "OpenAI (GPT-5.4 Mini)"}


def wilson(k, n, z=1.96):
    if not n:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def two_prop_z(k1, n1, k2, n2):
    """Two-proportion z test, for whether two providers actually differ."""
    if not n1 or not n2:
        return float("nan"), float("nan")
    p1, p2 = k1 / n1, k2 / n2
    p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return float("nan"), float("nan")
    z = (p1 - p2) / se
    pv = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return z, pv


def main() -> int:
    # verdict per run, recovered from disk (canonical path only, matching the
    # harness, so this reproduces what the paper's pipeline could have seen)
    abst = {r["run_dir"]: r for r in json.load(open(os.path.join(Q, "verifier_abstention.json")))}

    runs = {}
    with open(os.path.join(REPO, "shared/role_ablation/results/per_run.jsonl")) as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            runs[(d.get("config"), d.get("task_id"), d.get("seed"))] = d   # dedup

    rows = []
    for d in runs.values():
        cfg = d.get("config") or ""
        if len(cfg) < 6 or cfg[5] not in PROV:
            continue
        a = abst.get(d.get("run_dir"))
        verdict = a["verdict"] if a else None
        rows.append({"provider": PROV[cfg[5]], "config": cfg,
                     "task": d.get("task_id"), "seed": d.get("seed"),
                     "grader_pass": bool(d.get("pass")),
                     "verdict": verdict,
                     "outcome": a["outcome"] if a else "NO_LOG"})

    print(f"role-mixing runs resolved to a Verifier provider: {len(rows)}\n")
    out = {}
    print(f"{'provider':26} {'gFAIL':>6} {'abstain':>9} "
          f"{'conditional':>18} {'abstain=accept':>18} {'abstain=reject':>18}")
    print("-" * 100)
    for p in sorted(PROV.values()):
        g = [r for r in rows if r["provider"] == p]
        gf = [r for r in g if not r["grader_pass"]]
        wv = [r for r in gf if r["verdict"] in ("pass", "fail")]
        fa = [r for r in wv if r["verdict"] == "pass"]
        miss = len(gf) - len(wv)
        cells = {
            "conditional": (len(fa), len(wv)),
            "abstain_as_accept": (len(fa) + miss, len(gf)),
            "abstain_as_reject": (len(fa), len(gf)),
        }
        out[p] = {"n_all": len(g), "n_grader_fail": len(gf),
                  "abstention_rate": miss / len(gf) if gf else None,
                  **{k: {"k": a, "n": b, "rate": a / b if b else None,
                         "ci95": wilson(a, b)} for k, (a, b) in cells.items()}}
        def fmt(k, n):
            if not n:
                return "n/a".rjust(18)
            lo, hi = wilson(k, n)
            return f"{100*k/n:5.1f}% [{100*lo:.0f},{100*hi:.0f}]".rjust(18)
        print(f"{p:26} {len(gf):>6} {100*miss/max(1,len(gf)):>8.1f}% "
              f"{fmt(*cells['conditional'])} {fmt(*cells['abstain_as_accept'])} "
              f"{fmt(*cells['abstain_as_reject'])}")
    print("-" * 100)

    print("\nRANKING BY EACH DENOMINATOR  (most permissive first)")
    for key, lbl in (("conditional", "conditional [as published]"),
                     ("abstain_as_accept", "abstention = accept"),
                     ("abstain_as_reject", "abstention = reject")):
        order = sorted((p for p in out if out[p][key]["rate"] is not None),
                       key=lambda p: -out[p][key]["rate"])
        print(f"  {lbl:28} " + "  >  ".join(
            f"{p.split()[0]} {100*out[p][key]['rate']:.0f}%" for p in order))

    print("\nDOES THE PUBLISHED ORDERING SURVIVE?  pairwise two-proportion tests")
    ps = sorted(out)
    for key, lbl in (("conditional", "conditional"), ("abstain_as_reject", "abstain=reject")):
        print(f"  {lbl}:")
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                a, b = out[ps[i]][key], out[ps[j]][key]
                z, pv = two_prop_z(a["k"], a["n"], b["k"], b["n"])
                sig = "significant" if pv < .05 else "NOT significant"
                print(f"    {ps[i].split()[0]:10} vs {ps[j].split()[0]:10} "
                      f"z={z:+6.2f}  p={pv:.4f}  {sig}")

    json.dump(out, open(os.path.join(Q, "verifier_provider_recomputed.json"), "w"), indent=1)
    print(f"\nwrote {os.path.join(Q, 'verifier_provider_recomputed.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
