#!/usr/bin/env python3
"""Consolidate every verifier measurement into one section-ready table.

Three failure modes were measured independently, each from a different artifact.
This joins them so the paper's verifier section can be written from a single
source, and so a reviewer can trace every number to the script that produced it.

  LENIENCY      the verdict is wrong in the permissive direction
                sources: human verifierDecisions (Firebase), role-mixing grid
  CAPITULATION  a correct reject is reversed on an unchanged artifact
                source:  scripts/llm_capitulation.py, human decision sequences
  ABSTENTION    no verdict is filed at all
                source:  scripts/verifier_abstention.py

Everything here is recomputed from the stored artifacts; nothing is transcribed
from prose. Where an input is missing the row is reported as unavailable rather
than dropped, so the table cannot silently shrink.
"""
from __future__ import annotations

import json
import math
import os
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(REPO, "shared", "paper", "quality")
SCRATCH = ("/tmp/claude-17609/-u-ybkim95-TeamBench/"
           "7c206a77-7dfb-4ecd-809d-2e54383eace8/scratchpad")


def wilson(k, n, z=1.96):
    if not n:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def load(path, default=None):
    try:
        return json.load(open(path))
    except Exception:
        return default


def pct(k, n):
    if not n:
        return "n/a"
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100*k/n:.1f}% [{100*lo:.0f}, {100*hi:.0f}]"


def main() -> int:
    out = {"generated_from": {}, "leniency": {}, "capitulation": {},
           "abstention": {}, "notes": []}

    # ---- LENIENCY -------------------------------------------------------
    hv = load(os.path.join(SCRATCH, "verifier_full.json"), [])
    lv = load(os.path.join(SCRATCH, "llm_verifier_runs.json"), [])
    out["generated_from"]["human_decisions"] = len(hv)
    out["generated_from"]["llm_runs_with_verdict"] = len(lv)

    hgf = [r for r in hv if r.get("grader") == "fail"]
    hfa = [r for r in hgf if r.get("verdict") == "pass"]
    lgf = [r for r in lv if not r.get("grader_pass")]
    lfa = [r for r in lgf if r.get("verifier") == "pass"]
    out["leniency"]["human_false_accept"] = {"k": len(hfa), "n": len(hgf),
                                             "rate": len(hfa) / len(hgf) if hgf else None,
                                             "ci95": wilson(len(hfa), len(hgf))}
    out["leniency"]["llm_false_accept"] = {"k": len(lfa), "n": len(lgf),
                                           "rate": len(lfa) / len(lgf) if lgf else None,
                                           "ci95": wilson(len(lfa), len(lgf))}
    hs = [r["grader_score"] for r in hfa if isinstance(r.get("grader_score"), (int, float))]
    ls = [r["partial"] for r in lfa if isinstance(r.get("partial"), (int, float))]
    for lbl, s in (("human", hs), ("llm", ls)):
        if s:
            out["leniency"][f"{lbl}_approved_score"] = {
                "n": len(s), "median": statistics.median(s),
                "frac_below_0.5": sum(1 for x in s if x < .5) / len(s),
                "frac_below_0.3": sum(1 for x in s if x < .3) / len(s)}

    # ---- CAPITULATION ---------------------------------------------------
    cap = load(os.path.join(Q, "llm_capitulation.json"), [])
    flips = [r for r in cap if r.get("fail_then_pass")]
    known = [r for r in flips if r.get("workspace_changed_after_last_fail") is not None]
    caps = [r for r in known if r.get("capitulation")]
    out["capitulation"]["llm"] = {"runs_multi_attempt": len(cap),
                                  "fail_then_pass": len(flips),
                                  "resolvable": len(known), "capitulated": len(caps),
                                  "ci95": wilson(len(caps), len(known))}
    coded = load(os.path.join(REPO, "human_eval", "coding", "coding_coder1.json"), [])
    hcap = [r for r in coded if r.get("code") == "C1"]
    hfa_coded = [r for r in coded if r.get("verdict_human") == "pass"]
    out["capitulation"]["human"] = {"false_accepts": len(hfa_coded),
                                    "capitulated": len(hcap),
                                    "ci95": wilson(len(hcap), len(hfa_coded))}

    # ---- ABSTENTION -----------------------------------------------------
    ab = load(os.path.join(Q, "verifier_abstention.json"), [])
    if ab:
        n = len(ab)
        by = {}
        for r in ab:
            by[r["outcome"]] = by.get(r["outcome"], 0) + 1
        out["abstention"]["outcome_counts"] = by
        out["abstention"]["n"] = n
        out["abstention"]["no_usable_verdict_rate"] = (
            sum(by.get(k, 0) for k in ("ABSTAINED", "QUIT_EARLY", "MALFORMED")) / n)
        gf = [r for r in ab if r.get("grader_pass") is False]
        wv = [r for r in gf if r.get("verdict") in ("pass", "fail")]
        fa = [r for r in wv if r["verdict"] == "pass"]
        miss = len(gf) - len(wv)
        out["abstention"]["false_accept_under_treatment"] = {
            "excluded": {"k": len(fa), "n": len(wv), "ci95": wilson(len(fa), len(wv))},
            "as_accept": {"k": len(fa) + miss, "n": len(gf),
                          "ci95": wilson(len(fa) + miss, len(gf))},
            "as_reject": {"k": len(fa), "n": len(gf), "ci95": wilson(len(fa), len(gf))}}

    # ---- PROMPT SENSITIVITY (partial runs are fine, it is labelled) ------
    vps_p = os.path.join(Q, "verifier_prompt_sensitivity.jsonl")
    if os.path.isfile(vps_p):
        rows = [json.loads(l) for l in open(vps_p)]
        arms = {}
        for pr in ("lenient", "neutral", "strict"):
            g = [r for r in rows if r["prompt"] == pr]
            if not g:
                continue
            def v(r):
                return r.get("verdict") or r.get("verdict_forced")
            wv = [r for r in g if v(r) in ("pass", "fail")]
            gf = [r for r in wv if not r["grader_pass"]]
            fa = [r for r in gf if v(r) == "pass"]
            nat = sum(1 for r in g if r.get("verdict") in ("pass", "fail"))
            arms[pr] = {"n_runs": len(g), "with_verdict": len(wv),
                        "natural_verdict_rate": nat / len(g),
                        "grader_fail": len(gf), "false_accept": len(fa),
                        "rate": len(fa) / len(gf) if gf else None,
                        "ci95": wilson(len(fa), len(gf))}
        out["leniency"]["prompt_arms"] = arms
        out["notes"].append(f"prompt sensitivity read at {len(rows)}/180 rows; "
                            "rerun after completion for final values")

    json.dump(out, open(os.path.join(Q, "verifier_synthesis.json"), "w"), indent=1)

    # ---- print the section-ready table ----------------------------------
    L, C, A = out["leniency"], out["capitulation"], out["abstention"]
    print("=" * 78)
    print("VERIFIER FAILURE MODES")
    print("=" * 78)
    print("\n1. LENIENCY  (verdict wrong in the permissive direction)")
    for who, key in (("human", "human_false_accept"), ("LLM", "llm_false_accept")):
        d = L.get(key, {})
        print(f"   {who:6} false accept on grader-failing work: {pct(d.get('k',0), d.get('n',0))}")
    for who in ("human", "llm"):
        d = L.get(f"{who}_approved_score")
        if d:
            print(f"   {who:6} approved-score median {d['median']:.2f}, "
                  f"below 0.5 {100*d['frac_below_0.5']:.0f}%, below 0.3 {100*d['frac_below_0.3']:.0f}%")
    if L.get("prompt_arms"):
        print("\n   prompt sensitivity (artifact fixed, instruction varied):")
        for pr, d in L["prompt_arms"].items():
            r = f"{100*d['rate']:.1f}%" if d["rate"] is not None else "n/a"
            print(f"     {pr:8} {pct(d['false_accept'], d['grader_fail']):28} "
                  f"natural-verdict {100*d['natural_verdict_rate']:.0f}%")

    print("\n2. CAPITULATION  (correct reject reversed on an unchanged artifact)")
    h, l = C.get("human", {}), C.get("llm", {})
    print(f"   human {pct(h.get('capitulated',0), h.get('false_accepts',0))} of false accepts")
    print(f"   LLM   {pct(l.get('capitulated',0), l.get('resolvable',0))} of resolvable flips "
          f"({l.get('fail_then_pass',0)} flips in {l.get('runs_multi_attempt',0)} multi-attempt runs)")

    print("\n3. ABSTENTION  (no verdict filed)")
    if A:
        b = A["outcome_counts"]
        n = A["n"]
        for k in ("VERDICT", "ABSTAINED", "QUIT_EARLY", "MALFORMED", "MISPLACED"):
            print(f"   {k:11} {b.get(k,0):5}  {100*b.get(k,0)/n:5.1f}%")
        print(f"   no usable verdict: {100*A['no_usable_verdict_rate']:.1f}% of {n} runs")
        t = A["false_accept_under_treatment"]
        print("\n   headline false-accept depends on how abstentions are treated:")
        for lbl, key in (("excluded (as published)", "excluded"),
                         ("counted as accept", "as_accept"),
                         ("counted as reject", "as_reject")):
            d = t[key]
            print(f"     {lbl:26} {pct(d['k'], d['n'])}")
    print("\nwrote", os.path.join(Q, "verifier_synthesis.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
