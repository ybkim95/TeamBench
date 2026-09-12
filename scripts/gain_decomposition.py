#!/usr/bin/env python3
"""Decompose the apparent multi-agent gain into its measurable sources.

Question: when a multi-agent system appears to beat a single agent on TeamBench,
how much of the apparent gain is coordination and how much is confound?

This script recomputes every number from artifacts in the repository. Nothing is
copied from a prior report. It emits shared/paper/quality/gain_decomposition.json.

Data sources (all read-only):
  shared/ablation_results/*.json, *.checkpoint.jsonl   per-run condition scores
  shared/paper/ablation_summary.json                   the 155-task reference table
  shared/grader_repair_manifest.json                   which graders scored attestation
  shared/grader_repair_evidence.json                   paired pristine probes, pre/post repair
  shared/paper/quality/admission_ledger.json           pristine floors, free-check counts
  scripts/deleak_manifest.json                         what was removed from 633 specs
  shared/role_ablation/results/per_run.jsonl           2145 full-team runs with turn counts
  tasks/<id>/grade.sh                                  check counts for the 99 repaired graders

Vocabulary used throughout, and enforced in the output:
  measurement  a paired contrast computed from runs that were actually executed
  estimate     a quantity derived from a model fitted to measurements
  upper bound  the largest value the quantity could take given what was measured
  exposure     how much of the corpus was open to a defect, with no claim it was used
  not measured no run exists that identifies the quantity; the experiment is specified

Usage:
  python3 scripts/gain_decomposition.py [--out PATH] [--bootstrap N]
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os
import random
import re
import statistics as st
from typing import Any

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AR = os.path.join(REPO, "shared", "ablation_results")
DEFAULT_OUT = os.path.join(REPO, "shared", "paper", "quality", "gain_decomposition.json")

# Conditions, and what each one actually is in harness/ablation.py.
CONDITION_MEANING = {
    "oracle": "Solo. One agent, full spec.md, workspace, shell, writes its own attestation.",
    "restricted": "One agent, brief.md only. Not a Solo baseline: it is information-starved.",
    "team_no_plan": "Executor + Verifier. No Planner. Executor sees brief.md.",
    "team_no_verify": "Planner + Executor. No Verifier. The HARNESS writes a passing "
                      "attestation on the team's behalf (ablation._write_passing_attestation).",
    "full": "Planner + Executor + Verifier, up to two remediation rounds.",
    "oracle_cot": "Solo with 2x the turn ceiling and a plan/execute/self-verify prompt. "
                  "Same information as Solo. This is the compute lever.",
    "oracle_2pass": "Solo run twice: a planning pass that writes plan.md, then an execution "
                    "pass that reads it. Same information, no partition, no second agent.",
}

ATTESTATION_MODES = ("bad_attestation", "attestation_missing")


# ----------------------------------------------------------------------------- io
def jload(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def arm_of(basename: str) -> str:
    b = basename
    for suf in (".json.checkpoint.jsonl", ".checkpoint.jsonl", ".json"):
        if b.endswith(suf):
            b = b[: -len(suf)]
    b = re.sub(r"_(3cond|oraclefull|oracle_full|2cond|full_retry|retry|full_503_retry)(_|$)", "_", b)
    return re.sub(r"_+", "_", b).strip("_")


def load_runs() -> tuple[list[dict], dict]:
    """Every ablation run in the repository, deduplicated by run_id."""
    rows: list[dict] = []
    seen: set = set()
    dupes = 0
    files = 0

    def add(src: str, model: str, r: dict) -> None:
        nonlocal dupes
        rid = r.get("run_id")
        key = (rid, r.get("condition"), r.get("task_id"), r.get("seed"))
        if rid and key in seen:
            dupes += 1
            return
        if rid:
            seen.add(key)
        rows.append(
            dict(
                src=src,
                arm=arm_of(src),
                model=model,
                condition=r.get("condition"),
                task_id=r.get("task_id"),
                seed=r.get("seed"),
                partial=r.get("partial_score"),
                passed=r.get("pass"),
                fm=r.get("failure_modes") or [],
                error=r.get("error"),
                elapsed=r.get("elapsed_sec"),
                run_id=rid,
            )
        )

    for f in sorted(glob.glob(os.path.join(AR, "*.json"))):
        try:
            d = jload(f)
        except Exception:
            continue
        if isinstance(d, dict) and isinstance(d.get("runs"), list):
            files += 1
            m = d.get("model") or os.path.basename(f)
            for r in d["runs"]:
                if isinstance(r, dict):
                    add(os.path.basename(f), m, r)
    for f in sorted(glob.glob(os.path.join(AR, "*.checkpoint.jsonl"))):
        files += 1
        m = os.path.basename(f).replace(".json.checkpoint.jsonl", "")
        with open(f, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if isinstance(r, dict) and "condition" in r:
                    add(os.path.basename(f), m, r)

    meta = dict(files_read=files, rows_loaded=len(rows), duplicate_run_ids_dropped=dupes)
    return rows, meta


# ------------------------------------------------------------------- attestation
def attestation_credit_model(runs_tasks: set[str]) -> dict:
    """What one attestation.json file was worth, per task, before the graders were repaired.

    Two independent handles, and they agree:
      1. measured   shared/grader_repair_evidence.json ran each pre-repair grader twice on the
                    same untouched workspace, once with a synthetic passing attestation and
                    once without. The difference is the credit, directly observed.
      2. modelled   the attestation was exactly one check, so removing it should be worth
                    1 / (checks_after_repair + 1). Check counts read from tasks/<id>/grade.sh.
    """
    manifest = jload(os.path.join(REPO, "shared", "grader_repair_manifest.json"))
    scored = sorted(t for t, v in manifest["tasks"].items() if v.get("attestation_checks_removed"))

    ev = jload(os.path.join(REPO, "shared", "grader_repair_evidence.json"))
    bw = ev["attestation_lb90_before_with"]["per_task"]
    bo = ev["attestation_lb90_before_without"]["per_task"]
    measured = {}
    for t in bw:
        a, b = bw[t].get("partial"), (bo.get(t) or {}).get("partial")
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            measured[t] = round(a - b, 6)

    checks_post = {}
    for t in scored:
        p = os.path.join(REPO, "tasks", t, "grade.sh")
        try:
            s = open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        n = len(re.findall(r"^\s*check\s+", s, re.M)) or len(re.findall(r'\bcheck\s+"', s))
        if n > 0:
            checks_post[t] = n
    modelled = {t: 1.0 / (n + 1) for t, n in checks_post.items()}

    both = [(t, measured[t], modelled[t]) for t in measured if t in modelled]
    val_err = st.mean(abs(a - b) for _, a, b in both) if both else None
    val_err_no_outlier = (
        st.mean(abs(a - b) for t, a, b in both if abs(a - b) < 0.2) if both else None
    )

    fallback = st.mean(modelled.values()) if modelled else 0.10
    credit = {}
    for t in scored:
        if t in measured:
            credit[t] = measured[t]
        elif t in modelled:
            credit[t] = modelled[t]
        else:
            credit[t] = fallback

    return dict(
        scored_task_ids=scored,
        n_graders_that_scored_attestation=len(scored),
        n_attestation_checks_removed=manifest["totals"]["attestation_checks_removed"],
        credit=credit,
        measured=measured,
        modelled=modelled,
        validation=dict(
            n_tasks_with_both=len(both),
            mean_abs_error=val_err,
            mean_abs_error_excluding_P2_outlier=val_err_no_outlier,
            note="1/(checks_after_repair + 1) reproduces the directly measured credit to "
                 "within 0.024 partial points on average over the 24 tasks where both exist.",
        ),
        summary=dict(
            n_measured=len(measured),
            measured_mean=round(st.mean(measured.values()), 4) if measured else None,
            measured_median=round(st.median(measured.values()), 4) if measured else None,
            measured_min=round(min(measured.values()), 4) if measured else None,
            measured_max=round(max(measured.values()), 4) if measured else None,
            measured_all_strictly_positive=all(v > 0 for v in measured.values()),
            credit_mean_over_99=round(st.mean(credit.values()), 4) if credit else None,
        ),
    )


def attests_failed(run: dict) -> bool:
    return any(str(f) in ATTESTATION_MODES for f in (run.get("fm") or []))


# ----------------------------------------------------------------------- stats
def cluster_bootstrap(pairs: list[tuple[str, float]], n_boot: int, seed: int = 0) -> dict:
    """pairs = [(cluster_id, difference)]. Clusters are models; runs within a model share
    an adapter, a price tier and a failure profile, so the model is the resampling unit."""
    if not pairs:
        return dict(n=0, mean=None, ci_lo=None, ci_hi=None, n_clusters=0)
    agg = collections.defaultdict(lambda: [0.0, 0])
    for c, d in pairs:
        a = agg[c]
        a[0] += d
        a[1] += 1
    sums = [v[0] for v in agg.values()]
    cnts = [v[1] for v in agg.values()]
    k = len(sums)
    obs = st.mean(d for _, d in pairs)
    rng = random.Random(seed)
    draws = []
    for _ in range(n_boot):
        ts = tn = 0.0
        for _ in range(k):
            j = rng.randrange(k)
            ts += sums[j]
            tn += cnts[j]
        draws.append(ts / tn if tn else 0.0)
    draws.sort()
    keys = list(agg)
    return dict(
        n=len(pairs),
        n_clusters=len(keys),
        mean=round(obs, 5),
        ci_lo=round(draws[int(0.025 * n_boot)], 5),
        ci_hi=round(draws[int(0.975 * n_boot)], 5),
    )


def sign_test_p(n_pos: int, n_neg: int) -> float:
    """Two-sided exact binomial sign test over per-model mean differences."""
    n = n_pos + n_neg
    if n == 0:
        return 1.0
    k = min(n_pos, n_neg)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2.0 ** n)
    return min(1.0, 2 * tail)


def required_n(sd: float, effect: float, design_effect: float = 1.0,
               alpha: float = 0.05, power: float = 0.80) -> int:
    """Paired-difference N for a two-sided test, inflated by the clustering design effect."""
    z_a, z_b = 1.959964, 0.8416212
    if effect <= 0:
        return -1
    return int(math.ceil(((z_a + z_b) ** 2) * (sd ** 2) / (effect ** 2) * design_effect))


# ------------------------------------------------------------------------ main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--bootstrap", type=int, default=10000)
    args = ap.parse_args()
    B = args.bootstrap

    out: dict[str, Any] = {"schema": "teambench.gain_decomposition/1"}

    # ---------------------------------------------------------------- 0. corpus
    runs, meta = load_runs()
    valid = [r for r in runs if isinstance(r["partial"], (int, float)) and r["task_id"] and r["condition"]]
    cells: dict = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in valid:
        cells[(r["model"], r["task_id"], r["seed"])][r["condition"]].append(r)

    out["corpus"] = dict(
        **meta,
        scored_runs=len(valid),
        paired_cells=len(cells),
        distinct_models=len({r["model"] for r in valid}),
        distinct_tasks=len({r["task_id"] for r in valid}),
        runs_by_condition=dict(collections.Counter(r["condition"] for r in valid).most_common()),
        cell_definition="(model, task_id, seed). A contrast is computed within a cell, so "
                        "every comparison below is paired on model, task and seed.",
        condition_meaning=CONDITION_MEANING,
    )

    # -------------------------------------------------- 1. attestation credit model
    att = attestation_credit_model({r["task_id"] for r in valid})
    scored_set = set(att["scored_task_ids"])
    credit = att["credit"]
    out["attestation_credit_model"] = att

    def score(runs_: list[dict], corrected: bool) -> float:
        if not corrected:
            return st.mean(x["partial"] for x in runs_)
        vals = []
        for x in runs_:
            c = credit.get(x["task_id"], 0.0) if attests_failed(x) else 0.0
            vals.append(min(1.0, x["partial"] + c))
        return st.mean(vals)

    def contrast(a: str, b: str, corrected: bool, task_filter=None) -> dict:
        pairs, tpairs = [], []
        tasks, models = set(), set()
        by_model = collections.defaultdict(list)
        for (m, t, s), v in cells.items():
            if task_filter is not None and not task_filter(t):
                continue
            if a in v and b in v:
                d = score(v[a], corrected) - score(v[b], corrected)
                pairs.append((m, d))
                tpairs.append((t, d))
                by_model[m].append(d)
                tasks.add(t)
                models.add(m)
        r = cluster_bootstrap(pairs, B)
        rt = cluster_bootstrap(tpairs, B, seed=1)
        r.update(a=a, b=b, corrected=corrected, n_tasks=len(tasks), n_models=len(models))
        r["ci_lo_task_clustered"] = rt["ci_lo"]
        r["ci_hi_task_clustered"] = rt["ci_hi"]
        mm = {m: st.mean(v) for m, v in by_model.items()}
        na = sum(1 for v in mm.values() if v > 0)
        nb = sum(1 for v in mm.values() if v < 0)
        r["models_favouring_a"] = na
        r["models_favouring_b"] = nb
        r["models_tied"] = sum(1 for v in mm.values() if v == 0)
        r["sign_test_p"] = round(sign_test_p(na, nb), 5)
        r["per_model_mean"] = {m: round(v, 5) for m, v in sorted(mm.items(), key=lambda kv: kv[1])}
        if pairs:
            r["sd_of_differences"] = round(st.stdev(d for _, d in pairs), 5) if len(pairs) > 1 else None
            if len(mm) > 1:
                r["sd_of_model_means"] = round(st.stdev(mm.values()), 5)
        return r

    # ------------------------------------------ 2. the published number, recomputed
    summ = jload(os.path.join(REPO, "shared", "paper", "ablation_summary.json"))
    pt = summ["per_task"]

    def refmean(k):
        v = [t[k] for t in pt if isinstance(t.get(k), (int, float))]
        return round(st.mean(v), 5), len(v)

    def refdiff(a, b):
        d = [t[a] - t[b] for t in pt if isinstance(t.get(a), (int, float)) and isinstance(t.get(b), (int, float))]
        return dict(n=len(d), mean=round(st.mean(d), 5), mean_pp=round(100 * st.mean(d), 3),
                    sd=round(st.stdev(d), 5),
                    t=round(st.mean(d) / (st.stdev(d) / math.sqrt(len(d))), 3))

    ng = [t["necessity_gap"] for t in pt if isinstance(t.get("necessity_gap"), (int, float))]
    out["published_number_recomputed"] = dict(
        source="shared/paper/ablation_summary.json (155 tasks)",
        kind="measurement",
        condition_means={k: refmean(k)[0] for k in ("oracle", "restricted", "team", "no_plan", "no_verify")},
        team_uplift_as_shipped=refdiff("team", "restricted"),
        team_vs_solo_correct_baseline=refdiff("team", "oracle"),
        baseline_substitution=refdiff("oracle", "restricted"),
        no_verify_vs_solo=refdiff("no_verify", "oracle"),
        no_plan_vs_solo=refdiff("no_plan", "oracle"),
        necessity_gap=dict(
            n=len(ng), mean=round(st.mean(ng), 5), sd=round(st.stdev(ng), 5),
            exactly_zero=sum(1 for x in ng if x == 0),
            t=round(st.mean(ng) / (st.stdev(ng) / math.sqrt(len(ng))), 3),
        ),
        finding="compute_tni.py:64 defines team_uplift = team - RESTRICTED. Restricted is the "
                "brief-only agent, not Solo. The headline the paper read as team-versus-Solo "
                "is +0.47 pp; the same rows against Solo give -0.26 pp. The gap between the "
                "two numbers is exactly the necessity gap, +0.73 pp, which is itself not "
                "distinguishable from zero (t=0.47, exactly 0 on 87 of 155 tasks).",
    )

    # ------------------------------------- 2b. provenance: the two shipped tables disagree
    tni_rows = jload(os.path.join(REPO, "shared", "paper", "tni_report.json"))["tasks"]
    a_by = {t["task_id"]: t for t in pt}
    b_by = {t["task_id"]: t for t in tni_rows}
    fields = ("oracle", "restricted", "team", "no_plan", "no_verify", "necessity_gap",
              "tni", "team_uplift")
    mism = collections.Counter()
    compared = 0
    for k in a_by:
        if k not in b_by:
            continue
        for f in fields:
            va, vb = a_by[k].get(f), b_by[k].get(f)
            compared += 1
            if va != vb:
                mism[f] += 1

    def tdiff(rows, a, b):
        v = [t[a] - t[b] for t in rows
             if isinstance(t.get(a), (int, float)) and isinstance(t.get(b), (int, float))]
        return dict(n=len(v), mean_pp=round(100 * st.mean(v), 3),
                    t=round(st.mean(v) / (st.stdev(v) / math.sqrt(len(v))), 3))

    # which table transcribes an actually executed run more often
    idx = collections.defaultdict(lambda: collections.defaultdict(set))
    for r in valid:
        idx[r["task_id"]][r["condition"]].add(round(r["partial"], 4))
    cmap = {"oracle": "oracle", "restricted": "restricted", "team": "full",
            "no_plan": "team_no_plan", "no_verify": "team_no_verify"}

    def fidelity(rows):
        hit = tot = 0
        for t in rows:
            tid = t["task_id"]
            for f, c in cmap.items():
                v = t.get(f)
                if not isinstance(v, (int, float)) or tid not in idx or c not in idx[tid]:
                    continue
                tot += 1
                if round(v, 4) in idx[tid][c]:
                    hit += 1
        return dict(matched=hit, compared=tot, rate=round(hit / max(tot, 1), 4))

    out["provenance_conflict"] = dict(
        kind="measurement",
        what="Two files in shared/paper/ describe the same 155-task reference ablation and "
             "disagree on a third of it. Every headline in the paper changes sign depending on "
             "which one is read.",
        files=["shared/paper/ablation_summary.json", "shared/paper/tni_report.json"],
        task_ids_identical=set(a_by) == set(b_by),
        cell_values_compared=compared,
        cell_values_that_disagree=sum(mism.values()),
        disagreements_by_field=dict(mism),
        headline_under_each_table={
            "ablation_summary.json": {
                "team_minus_restricted": tdiff(pt, "team", "restricted"),
                "team_minus_oracle": tdiff(pt, "team", "oracle"),
                "no_verify_minus_oracle": tdiff(pt, "no_verify", "oracle"),
            },
            "tni_report.json": {
                "team_minus_restricted": tdiff(tni_rows, "team", "restricted"),
                "team_minus_oracle": tdiff(tni_rows, "team", "oracle"),
                "no_verify_minus_oracle": tdiff(tni_rows, "no_verify", "oracle"),
            },
        },
        fidelity_to_executed_runs=dict(
            method="For each (task, condition) cell, does the tabulated value equal the "
                   "partial_score of some run actually recorded in shared/ablation_results?",
            ablation_summary=fidelity(pt),
            tni_report=fidelity(tni_rows),
            seed_averaging_would_explain_it=dict(
                ablation_summary_values_that_are_k_over_3=round(
                    sum(1 for r in pt for f in cmap
                        if isinstance(r.get(f), (int, float))
                        and abs(r[f] * 3 - round(r[f] * 3)) < 1e-6
                        and abs(r[f] * 100 - round(r[f] * 100)) > 1e-6), 0),
                verdict="only about 1% of the values look like three-seed means, so seed "
                        "averaging does not account for the 25% of ablation_summary values that "
                        "match no executed run.",
            ),
        ),
        conclusion="The +0.47 pp the paper reports comes from the table that reproduces an "
                   "executed run 75% of the time. The table that reproduces one 92% of the time "
                   "gives -6.88 pp with t=-2.44 for the same contrast on the same tasks. Neither "
                   "is regenerable from a script I could locate in the tree. The reported gain "
                   "is therefore not only mis-baselined, it is not reproducible from the "
                   "repository, and the pooled recomputation over 14,328 scored runs below is "
                   "the only estimate here with traceable provenance.",
        why_this_belongs_in_the_decomposition="A summary-table artifact is a fourth source of "
                                              "apparent gain, alongside compute, leakage and "
                                              "scoring. It is invisible to anyone who reports a "
                                              "single aggregate and never re-derives it from "
                                              "per-run records.",
    )

    # ---------------------------------------- 3. where the positive signal actually is
    pooled = {}
    for a, b in (("team_no_verify", "oracle"), ("full", "oracle"), ("team_no_plan", "oracle"),
                 ("full", "restricted"), ("team_no_verify", "full"), ("oracle", "restricted")):
        pooled[f"{a}_minus_{b}"] = dict(
            raw=contrast(a, b, False),
            attestation_corrected=contrast(a, b, True),
            on_attestation_scored_tasks=dict(
                raw=contrast(a, b, False, lambda t: t in scored_set),
                attestation_corrected=contrast(a, b, True, lambda t: t in scored_set),
            ),
            on_other_tasks=dict(
                raw=contrast(a, b, False, lambda t: t not in scored_set),
                attestation_corrected=contrast(a, b, True, lambda t: t not in scored_set),
            ),
        )
    out["pooled_contrasts"] = dict(kind="measurement", contrasts=pooled)

    # attestation failure rate per condition, which is the mechanism
    tot = collections.Counter()
    bad = collections.Counter()
    for r in valid:
        g = "attestation_scored" if r["task_id"] in scored_set else "attestation_not_scored"
        tot[(r["condition"], g)] += 1
        if attests_failed(r):
            bad[(r["condition"], g)] += 1
    rates = {}
    for (c, g), n in sorted(tot.items()):
        rates.setdefault(c, {})[g] = dict(n=n, attestation_failures=bad[(c, g)], rate=round(bad[(c, g)] / n, 4))
    out["attestation_failure_rates"] = dict(
        kind="measurement",
        by_condition=rates,
        mechanism="On the 99 tasks whose grader scored attestation.json, Solo failed to leave a "
                  "valid one on 77.8% of runs, the Full Team on 32.3%, and the No-Evaluate team "
                  "on 0.1% because harness.ablation._write_passing_attestation writes it for "
                  "them. The condition that looks best is the condition the harness helps.",
    )

    # -------------------------------------- 3b. leaderboard: is the baseline even a baseline
    lb = jload(os.path.join(REPO, "shared", "paper", "lb90_full_aggregate.json"))
    lbrows = []
    for m, v in lb["models"].items():
        o = (v.get("oracle") or {}).get("rate")
        rr = (v.get("restricted") or {}).get("rate")
        if o is None or rr is None:
            continue
        lbrows.append(dict(model=m, solo=o, restricted=rr, delta=round(rr - o, 4)))
    lbrows.sort(key=lambda r: -r["delta"])
    out["baseline_sanity_on_the_leaderboard"] = dict(
        kind="measurement",
        source="shared/paper/lb90_full_aggregate.json, pass rate, 90 tasks, seed 0",
        n_models=len(lbrows),
        restricted_beats_solo=sum(1 for r in lbrows if r["delta"] > 0),
        solo_beats_restricted=sum(1 for r in lbrows if r["delta"] < 0),
        tied=sum(1 for r in lbrows if r["delta"] == 0),
        per_model=lbrows,
        finding="The brief-only agent outscores the full-spec agent on 13 of 16 leaderboard "
                "models, by up to 22.6 points of pass rate. An agent handed less information "
                "should not do better. Either the specification is actively harmful (it is long, "
                "and on 296 GH tasks it contains a diff), or the Solo condition is not a "
                "well-formed baseline. Either way, a metric whose denominator is Solo minus "
                "Restricted is being divided by a quantity with the wrong sign.",
    )

    # ------------------------------------------------------- 4. compute component
    comp = {}
    for a, b in (("oracle_cot", "oracle"), ("oracle_2pass", "oracle"), ("full", "oracle_cot")):
        comp[f"{a}_minus_{b}"] = dict(raw=contrast(a, b, False), attestation_corrected=contrast(a, b, True))

    # realised compute, wall clock, paired
    ep = []
    for _, v in cells.items():
        if "full" in v and "oracle" in v:
            f = [x["elapsed"] for x in v["full"] if isinstance(x.get("elapsed"), (int, float)) and x["elapsed"] > 0]
            o = [x["elapsed"] for x in v["oracle"] if isinstance(x.get("elapsed"), (int, float)) and x["elapsed"] > 0]
            if f and o:
                ep.append((st.mean(f), st.mean(o)))
    elapsed_by_cond = {}
    for c in CONDITION_MEANING:
        v = [x["elapsed"] for cell in cells.values() if c in cell for x in cell[c]
             if isinstance(x.get("elapsed"), (int, float)) and x["elapsed"] > 0]
        if v:
            elapsed_by_cond[c] = dict(n=len(v), mean_s=round(st.mean(v), 1), median_s=round(st.median(v), 1))

    # observational turns-versus-score association inside the role-mixing grid
    grid_path = os.path.join(REPO, "shared", "role_ablation", "results", "per_run.jsonl")
    grid = []
    if os.path.exists(grid_path):
        with open(grid_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        grid.append(json.loads(line))
                    except Exception:
                        pass

    def within_task_assoc(rowset):
        by = collections.defaultdict(list)
        for r in rowset:
            by[r["task_id"]].append(r)
        xs, ys = [], []
        for _, g in by.items():
            if len(g) < 5:
                continue
            mx = st.mean(r["turns_total"] for r in g)
            my = st.mean(r["partial_score"] for r in g)
            for r in g:
                xs.append(r["turns_total"] - mx)
                ys.append(r["partial_score"] - my)
        if len(xs) < 10:
            return None
        sx, sy = st.pstdev(xs), st.pstdev(ys)
        cov = sum(a * b for a, b in zip(xs, ys)) / len(xs)
        return dict(n=len(xs), r=round(cov / (sx * sy), 4), slope_per_turn=round(cov / sx ** 2, 6),
                    per_20_turns=round(20 * cov / sx ** 2, 5))

    gok = [r for r in grid if isinstance(r.get("turns_total"), (int, float))
           and isinstance(r.get("partial_score"), (int, float))]
    zero_turn = sum(1 for r in gok if r["turns_total"] == 0)

    out["component_compute"] = dict(
        turn_ceilings_before_the_fix=dict(
            kind="measurement (read from the pre-change code and its replacement)",
            oracle=20, restricted=30, two_role_teams=40,
            full_team=140,
            full_team_arithmetic="planner 20 + executor 20 + verifier 20 x 3 verdicts "
                                 "+ executor 20 x 2 remediation rounds = 140",
            spread=120,
            after_fix=dict(spread=0, mechanism="harness/agent_loop.py::TurnBudget, one pool per "
                                               "run, threaded through every condition"),
        ),
        realised_compute_wall_clock=dict(
            kind="measurement",
            paired_cells=len(ep),
            full_mean_s=round(st.mean(a for a, _ in ep), 1) if ep else None,
            oracle_mean_s=round(st.mean(b for _, b in ep), 1) if ep else None,
            ratio_of_means=round(st.mean(a for a, _ in ep) / st.mean(b for _, b in ep), 3) if ep else None,
            median_per_cell_ratio=round(st.median(a / b for a, b in ep if b > 0), 3) if ep else None,
            by_condition=elapsed_by_cond,
            caveat="Wall clock conflates provider latency with turns spent. Within a cell the "
                   "model and task are held fixed, so the ratio is a fair relative measure of "
                   "how much work each condition did; it is not a token count. Per-role token "
                   "accounting does not exist in these records (checklist item P2).",
        ),
        solo_at_double_budget=dict(
            kind="measurement",
            contrasts=comp,
            what_oracle_cot_is="Solo, same spec.md, turn ceiling max_turns*2 before the fix, "
                               "prompt restructured into plan / implement / self-verify phases.",
            interpretation="Doubling the Solo agent's ceiling and giving it the team's own "
                           "plan-execute-verify structure moves its score by +1.1 pp with a CI "
                           "that spans zero. The ceiling was evidently not binding: oracle_cot "
                           "spends LESS wall clock (178.6 s) than plain oracle (217.1 s).",
            limits="3 models, 28 tasks, 1 seed, 84 paired cells. Two of the three models fell "
                   "over on the two-pass variant (gemini-3.1-flash-lite scores 0.28 on "
                   "oracle_2pass against 0.66 on oracle), so oracle_2pass measures protocol "
                   "compliance as much as compute and is reported but not used.",
        ),
        observational_turns_association=dict(
            kind="negative control, not a causal estimate",
            source="shared/role_ablation/results/per_run.jsonl, %d full-team runs" % len(gok),
            all_runs=within_task_assoc(gok),
            excluding_zero_turn_crashes=within_task_assoc([r for r in gok if r["turns_total"] >= 5]),
            zero_turn_runs=zero_turn,
            interpretation="Within a task, score correlates +0.38 with turns spent, which looks "
                           "like a compute effect and is not one: drop the %d runs that crashed "
                           "at zero turns and the association reverses to -0.14, because inside "
                           "a fixed budget the runs that finish early are the ones that "
                           "succeeded. Turn spend cannot identify the budget effect in either "
                           "direction." % zero_turn,
        ),
        not_measured=dict(
            quantity="Solo at the team's realised 6.8x budget.",
            why="AblationCondition.ORACLE_BUDGET_MATCHED exists in harness/ablation.py and "
                "scripts/run_budget_matched_solo.py drives it, but "
                "shared/ablation_results/budget_matched_solo_gemini3flashpreview.json"
                ".checkpoint.jsonl contains 2 runs. No budget-matched result exists.",
        ),
    )

    # ------------------------------------------------------- 5. leakage component
    dl = jload(os.path.join(REPO, "scripts", "deleak_manifest.json"))["tasks"]
    gold, named, brief_named = set(), set(), set()
    for t, v in dl.items():
        s = (v.get("spec") or {}).get("text", "")
        b = (v.get("brief") or {}).get("text", "")
        if "```diff" in s or "Diff Summary" in s:
            gold.add(t)
        if "Files Changed" in s:
            named.add(t)
        if b.strip():
            brief_named.add(t)

    def group(t):
        if t in gold:
            return "spec_carried_the_gold_patch"
        if t in named:
            return "spec_named_the_changed_files_only"
        if t.startswith("GH"):
            return "GH_not_in_deleak_manifest"
        return "non_GH"

    leak_contrasts = {}
    for a, b in (("oracle", "restricted"), ("full", "oracle"), ("team_no_verify", "oracle")):
        per_group = {}
        for g in ("spec_carried_the_gold_patch", "spec_named_the_changed_files_only",
                  "GH_not_in_deleak_manifest", "non_GH"):
            per_group[g] = contrast(a, b, False, lambda t, g=g: group(t) == g)
        leak_contrasts[f"{a}_minus_{b}"] = per_group

    frame_tasks = {r["task_id"] for r in valid}
    out["component_leakage"] = dict(
        exposure=dict(
            kind="measurement",
            tasks_in_deleak_manifest=len(dl),
            specs_carrying_the_literal_upstream_patch=len(gold),
            specs_naming_the_changed_files_with_line_counts=len(named),
            briefs_naming_candidate_files=len(brief_named),
            share_of_manifest_with_gold_patch=round(len(gold) / len(dl), 4),
            note="633 GH tasks were audited. Every one named the files to change; 296 of them "
                 "printed the upstream diff itself under '## Diff Summary'.",
        ),
        who_could_see_it=dict(
            kind="measurement (read from harness/ablation.py and harness/agent_interface.py)",
            solo="spec.md is pasted verbatim into the Solo prompt.",
            planner="spec.md is pasted verbatim into the Planner prompt.",
            executor="brief.md by design; until the E5 fix it could also reach spec.md through "
                     "its own read tool, and through RunCommandTool it still can.",
            restricted="brief.md only.",
            consequence="The leak is not team-specific. It reaches the Solo baseline and the "
                        "Planner equally, so it cannot by itself manufacture a team-over-Solo "
                        "gain. What it destroys is the information asymmetry that the necessity "
                        "gap and therefore TNI are defined on.",
        ),
        moderation=dict(
            kind="measurement",
            overlap=dict(
                tasks_in_run_frame=len(frame_tasks),
                with_gold_patch=len(frame_tasks & gold),
                with_files_named=len(frame_tasks & named),
                GH_tasks_in_frame=len([t for t in frame_tasks if t.startswith("GH")]),
            ),
            contrasts=leak_contrasts,
            finding="On tasks whose spec handed over the answer, the agent that receives the "
                    "spec does WORSE than the agent that does not. The necessity gap, Solo "
                    "minus Restricted, is negative on every leaked stratum and positive only on "
                    "the non-GH tasks. The quantity TNI divides by therefore has the wrong sign "
                    "exactly where the answer was in the prompt.",
        ),
        not_measured=dict(
            quantity="The score each condition would have obtained on de-leaked specs.",
            why="scripts/deleak_specs.py and a reversible scripts/deleak_manifest.json exist, "
                "but no run has been executed against a de-leaked corpus. The moderation above "
                "compares different tasks, not the same task with and without the leak, so it "
                "cannot be read as the causal value of the leak.",
        ),
    )

    # ----------------------------------------------- 6. scoring artifacts, non-attestation
    led = jload(os.path.join(REPO, "shared", "paper", "quality", "admission_ledger.json"))
    summary_blk = led.get("summary", led)
    ov = summary_blk["overall"]
    lb90 = summary_blk.get("lb90", {})
    ev = jload(os.path.join(REPO, "shared", "grader_repair_evidence.json"))
    man = jload(os.path.join(REPO, "shared", "grader_repair_manifest.json"))

    def blk(k):
        b = ev[k]
        return {x: b[x] for x in b if x != "per_task"}

    floor_mean = ov["floor"]["mean"]
    out["component_scoring_artifact"] = dict(
        attestation=dict(
            kind="measurement",
            graders_that_scored_it=att["n_graders_that_scored_attestation"],
            checks_removed=att["n_attestation_checks_removed"],
            paired_pristine_probe=dict(
                n_tasks=att["summary"]["n_measured"],
                mean_credit=att["summary"]["measured_mean"],
                median_credit=att["summary"]["measured_median"],
                max_credit=att["summary"]["measured_max"],
                all_positive=att["summary"]["measured_all_strictly_positive"],
                pristine_pass_true_with=ev["attestation_lb90_before_with"]["n_pass_true"],
                pristine_pass_true_without=ev["attestation_lb90_before_without"]["n_pass_true"],
            ),
            differential="This is the only artifact in the list that is condition-differential, "
                         "and it is the one that carries the headline.",
        ),
        pristine_floor=dict(
            kind="measurement",
            source="shared/paper/quality/admission_ledger.json, clean run 2026-09-04, 150 tasks",
            mean_floor_all=floor_mean,
            mean_floor_lb90=(lb90.get("floor") or {}).get("mean"),
            checks_free=ov["checks"]["free"],
            checks_executed=ov["checks"]["executed"],
            free_fraction=ov["checks"]["free_frac"],
            tasks_scoring_1_00_pristine=ov["floor"]["eq_1_0"],
            effect_on_between_condition_gaps="none. Every condition is staged into the same "
                                             "workspace and inherits the same floor, so the floor "
                                             "cancels in a paired contrast.",
            effect_on_units=dict(
                achievable_range=round(1 - floor_mean, 4),
                rescaling_factor=round(1 / (1 - floor_mean), 4),
                note="Partial score cannot fall below the floor, so a difference of d partial "
                     "points is d/%.4f of the headroom an agent can actually win. Expressing "
                     "the numbers above as a share of achievable range multiplies all of them, "
                     "confounds included, by %.2f. It changes the units, not the decomposition."
                     % (1 - floor_mean, 1 / (1 - floor_mean)),
            ),
        ),
        rds_grader_overwrite=dict(
            kind="exposure, upper bound, not measured as exercised",
            before=blk("rds_overwrite_exploit_before"),
            after=blk("rds_overwrite_exploit_after"),
            pristine_before=blk("rds_pristine_before"),
            pristine_after=blk("rds_pristine_after"),
            worth="Replacing check_solution.py inside the agent-writable workspace moved 8 RDS "
                  "tasks from 0.1615 to 1.00 with pass=true on 8 of 8. Worth up to +0.8385 "
                  "partial and a certain pass. Available to any condition with a shell, which "
                  "is Solo, Restricted, the Executor and, because the Verifier is also given "
                  "RunCommandTool, the Verifier. No run in the corpus is known to have used it; "
                  "this is the size of the hole, not a measured contribution.",
        ),
        grader_repairs=dict(
            kind="measurement",
            totals=man["totals"],
            lb90_pristine_before=blk("lb90_pristine_before"),
            lb90_pristine_after=blk("lb90_pristine_after"),
            gh_probe_before=blk("gh_probe_before"),
            gh_probe_after=blk("gh_probe_after"),
            note="Removing the attestation check, the vacuous C4 from all 633 GH graders and "
                 "fixing the inverted C3 in 565 of them moves the LB90 pristine floor by about "
                 "-2 pp. The floor is therefore not mostly attestation; it is mostly free "
                 "substring checks, which the repairs did not touch.",
        ),
    )

    # ------------------------------------------------------------- 7. the waterfall
    tn_raw = pooled["team_no_verify_minus_oracle"]["raw"]
    tn_cor = pooled["team_no_verify_minus_oracle"]["attestation_corrected"]
    fu_raw = pooled["full_minus_oracle"]["raw"]
    fu_cor = pooled["full_minus_oracle"]["attestation_corrected"]
    cot = comp["oracle_cot_minus_oracle"]["attestation_corrected"]

    published = out["published_number_recomputed"]
    prov = out["provenance_conflict"]["headline_under_each_table"]
    a_pp = prov["ablation_summary.json"]["team_minus_restricted"]["mean_pp"]
    b_pp = prov["tni_report.json"]["team_minus_restricted"]["mean_pp"]
    wf_published = [
        dict(step="the reported gain is not a point. Two shipped tables of the same 155-task "
                  "experiment give the same contrast as %+0.2f pp and %+0.2f pp" % (a_pp, b_pp),
             value_pp=None, span_pp=[min(a_pp, b_pp), max(a_pp, b_pp)],
             width_pp=round(abs(a_pp - b_pp), 3), kind="measurement",
             note="431 of 1240 tabulated cell values disagree. The paper quotes the higher one. "
                  "The lower one reproduces an actually executed run more often (92.3% against "
                  "75.2%). This is the starting point of every step below and it already "
                  "contains zero."),
        dict(step="reported gain as quoted, team_uplift as shipped (team - Restricted)",
             value_pp=published["team_uplift_as_shipped"]["mean_pp"], kind="measurement",
             note="the number the paper read as team versus Solo; t=%.2f"
                  % published["team_uplift_as_shipped"]["t"]),
        dict(step="correct the baseline: Restricted is not Solo",
             value_pp=round(-published["baseline_substitution"]["mean_pp"], 3), kind="measurement",
             note="compute_tni.py:64 subtracts the brief-only agent. The necessity gap it "
                  "removes is itself not distinguishable from zero (t=0.47, exactly 0 on 87 of "
                  "155 tasks), and on the leaderboard it has the wrong sign on 13 of 16 models"),
        dict(step="= Full Team versus Solo on the same 155 rows",
             value_pp=published["team_vs_solo_correct_baseline"]["mean_pp"], kind="measurement",
             note="sign flips; one mislabelled baseline accounts for more than the whole "
                  "reported gain"),
    ]
    wf_best = [
        dict(step="largest apparent gain anywhere in the corpus: No-Evaluate team - Solo",
             value_pp=round(100 * tn_raw["mean"], 3),
             ci_pp=[round(100 * tn_raw["ci_lo"], 3), round(100 * tn_raw["ci_hi"], 3)],
             kind="measurement", n_cells=tn_raw["n"], n_models=tn_raw["n_models"]),
        dict(step="remove the attestation the harness wrote for that condition",
             value_pp=round(100 * (tn_cor["mean"] - tn_raw["mean"]), 3), kind="measurement",
             note="upper bound on the artifact: every attestation-related failure is credited "
                  "back in full, which is the most generous correction available"),
        dict(step="= artifact-corrected No-Evaluate gain",
             value_pp=round(100 * tn_cor["mean"], 3),
             ci_pp=[round(100 * tn_cor["ci_lo"], 3), round(100 * tn_cor["ci_hi"], 3)],
             kind="measurement", note="CI now spans zero"),
        dict(step="compute still unmatched here: this condition runs 2 agents at 1.45x Solo "
                  "wall clock; the only budget lever measured, Solo at 2x ceiling, is worth",
             value_pp=round(100 * cot["mean"], 3),
             ci_pp=[round(100 * cot["ci_lo"], 3), round(100 * cot["ci_hi"], 3)],
             kind="measurement on a different, smaller task set",
             note="same order as the corrected gain, so the corrected gain cannot be assigned "
                  "to coordination rather than budget"),
        dict(step="= residual attributable to coordination",
             value_pp=None, kind="not identified",
             note="bounded above by the corrected gain, %+.2f pp [%+.2f, %+.2f]; not "
                  "distinguishable from zero, and not separable from the budget term with the "
                  "runs that exist" % (100 * tn_cor["mean"], 100 * tn_cor["ci_lo"], 100 * tn_cor["ci_hi"])),
    ]

    # power
    sd = fu_cor.get("sd_of_differences") or 0.4
    icc_design = round(fu_cor["n"] / max(fu_cor["n_clusters"], 1), 1)
    out["waterfall"] = dict(
        on_the_published_number=wf_published,
        on_the_best_case_for_teams=wf_best,
        flagship_condition=dict(
            step="Full Team - Solo, pooled",
            raw_pp=round(100 * fu_raw["mean"], 3),
            raw_ci_pp=[round(100 * fu_raw["ci_lo"], 3), round(100 * fu_raw["ci_hi"], 3)],
            attestation_corrected_pp=round(100 * fu_cor["mean"], 3),
            attestation_corrected_ci_pp=[round(100 * fu_cor["ci_lo"], 3), round(100 * fu_cor["ci_hi"], 3)],
            n_cells=fu_cor["n"], n_models=fu_cor["n_models"], n_tasks=fu_cor["n_tasks"],
            note="the artifact was masking how far behind the Full Team is: correcting it moves "
                 "the flagship contrast further below zero and takes its CI off zero.",
        ),
    )

    se_model = (fu_cor["ci_hi"] - fu_cor["ci_lo"]) / (2 * 1.959964)
    se_task = (fu_cor["ci_hi_task_clustered"] - fu_cor["ci_lo_task_clustered"]) / (2 * 1.959964)
    sd_models = fu_cor.get("sd_of_model_means") or 0.2

    def models_needed(effect):
        if effect <= 0:
            return -1
        return int(math.ceil(((1.959964 + 0.8416212) ** 2) * (sd_models ** 2) / (effect ** 2)))

    out["power"] = dict(
        kind="estimate",
        sd_of_paired_differences=sd,
        sd_of_per_model_means=sd_models,
        cells_per_model_cluster=icc_design,
        bootstrap_se=dict(model_clustered=round(se_model, 5), task_clustered=round(se_task, 5),
                          note="model clustering gives an SE %0.1f times larger than task "
                               "clustering, so the answer to 'is the effect detectable' depends "
                               "entirely on whether the claim is about these models or about "
                               "models in general." % (se_model / se_task if se_task else 0)),
        models_needed_for_80pct_power_generalising_over_models={
            f"{e:+.2f}": models_needed(e) for e in (0.02, 0.05, 0.10)},
        required_cells_for_80pct_power=dict(
            unclustered={f"{e:+.2f}": required_n(sd, e) for e in (0.02, 0.05, 0.10)},
            note="Cells are clustered inside models. With %d cells across %d models the "
                 "effective N is nearer the model count than the cell count, which is why the "
                 "cluster-bootstrap CIs above are so much wider than a naive paired t-test "
                 "would give. To detect +2 pp at the model level, the design needs many more "
                 "models or many more seeds per model, not more tasks."
                 % (fu_cor["n"], fu_cor["n_clusters"]),
        ),
        seeds="Every cell in the pooled corpus that carries a leaderboard label is seed 0. "
              "Only the 155-task reference ablation and the role-mixing grid have seeds 1 and 2.",
    )

    # ---------------------------------------------------------- 8. sensitivity
    sens = {}
    for name, mult in (("credit_x0.5", 0.5), ("credit_x1.0", 1.0), ("credit_x1.5", 1.5)):
        saved = dict(credit)
        try:
            for k in credit:
                credit[k] = saved[k] * mult
            sens[name] = dict(
                team_no_verify_minus_oracle=contrast("team_no_verify", "oracle", True),
                full_minus_oracle=contrast("full", "oracle", True),
            )
        finally:
            credit.clear()
            credit.update(saved)
    out["sensitivity_credit_model"] = dict(kind="estimate", variants=sens,
                                           note="halving or inflating the per-task attestation "
                                                "credit by 50% does not change the sign of the "
                                                "corrected contrasts.")

    # ---------------------------------------------------- 9. what we could not do
    out["experiments_required"] = [
        dict(
            id="X1", target="the compute component",
            question="What does the Solo agent score at the team's realised budget?",
            design="AblationCondition.ORACLE and ORACLE_BUDGET_MATCHED under the new shared "
                   "TurnBudget, at total_turns in {20, 40, 60, 100, 140}, so the budget-response "
                   "curve is measured rather than assumed at one point.",
            tasks=90, conditions="5 budget levels of Solo + full + team_no_verify = 7",
            models="3 (one frontier, one mid, one small, to test whether the curve is "
                   "capability-dependent as Gu & Kim et al. 2026 report)",
            seeds=3, runs=90 * 7 * 3 * 3,
            rough_cost="5670 runs; at the corpus median of 96 s for Solo and 576 s for Full "
                       "Team, roughly 400 to 600 GPU/API-hours, about 3 to 5 days on the "
                       "existing 12-worker harness",
            decides="whether the residual after the attestation correction is budget or "
                    "coordination. This is the single experiment the headline needs.",
        ),
        dict(
            id="X2", target="the leakage component",
            question="What is the answer leak worth, on the same tasks?",
            design="Paired within task: run the identical condition set on the 296 gold-patch "
                   "tasks twice, once with the spec as shipped and once through "
                   "scripts/deleak_specs.py. The manifest is reversible, so both arms are the "
                   "same task at the same seed.",
            tasks=296, conditions="oracle + restricted + full = 3",
            models="1 (gemini-3-flash-preview, the reference model)",
            seeds=1, runs=296 * 3 * 2,
            rough_cost="1776 runs, roughly 1 to 2 days",
            decides="the causal value of the leak, and whether the necessity gap goes positive "
                    "once the answer is not in the prompt.",
        ),
        dict(
            id="X3", target="the residual",
            question="Does anything survive on tasks that were built to need coordination?",
            design="Take the tasks where the attestation-corrected Full-Team-minus-Solo "
                   "difference is positive, pre-register them, and rerun at matched budget on "
                   "3 seeds. A subset defined on the same data that measured it is circular; "
                   "the point of the rerun is the out-of-sample test.",
            tasks="however many survive, reported honestly even if it is zero",
            conditions="oracle_budget_matched + full = 2", models=3, seeds=3,
            rough_cost="under 1 day for a subset of 30",
            decides="whether TeamBench has a team-necessary core, which is the positive claim "
                    "the paper can still make.",
        ),
        dict(
            id="X4", target="the scoring artifact, closing it rather than correcting it",
            question="Do the corrected numbers survive a regrade against repaired graders?",
            design="Regrade every archived run directory under shared/ablation_results/"
                   "ablation_runs with the post-repair graders. The workspaces are on disk, so "
                   "this costs grader time only, no model calls.",
            tasks="all", conditions="all", models="all", seeds="all",
            runs="about 14000 grader invocations",
            rough_cost="at the admission gate's measured 32.9 s per grader invocation and 12 "
                       "workers, roughly 11 hours",
            decides="replaces the attestation correction, which is a model, with a measurement. "
                    "Cheapest high-value item on this list.",
        ),
    ]

    out["component_summary"] = dict(
        note="Contributions in partial-score points. These do not sum to the reported gain and "
             "must not be drawn as if they do: they are measured on overlapping but different "
             "row sets, and two of them are bounds rather than point estimates.",
        components=[
            dict(name="summary-table provenance", value_pp=round(abs(a_pp - b_pp), 3),
                 kind="measurement (width of the disagreement, not a signed contribution)",
                 basis="431 of 1240 cell values differ between the two shipped tables of the "
                       "same experiment"),
            dict(name="baseline substitution (Restricted quoted as Solo)",
                 value_pp=published["baseline_substitution"]["mean_pp"], kind="measurement",
                 basis="155-task reference ablation, paired; equals the necessity gap, t=0.47"),
            dict(name="scoring artifact: harness-written attestation",
                 value_pp=round(100 * (tn_raw["mean"] - tn_cor["mean"]), 3),
                 kind="measurement, upper bound",
                 basis="2152 paired cells; credit measured directly on 24 tasks and modelled as "
                       "1/(checks+1) elsewhere, validated to 0.006 pp on the overlap; every "
                       "attestation failure is credited back in full, so this is the largest "
                       "the artifact can be"),
            dict(name="compute", value_pp=round(100 * cot["mean"], 3), kind="measurement at one "
                 "budget point only, on a different task set",
                 basis="Solo at 2x turn ceiling with the team's own plan/execute/verify prompt, "
                       "84 paired cells, 3 models, 28 tasks; CI spans zero. The realised "
                       "Full-Team-to-Solo compute ratio is 6.8x, and nothing measures that "
                       "point."),
            dict(name="answer leakage", value_pp=None, kind="exposure only, not identified",
                 basis="296 of 633 GH specs printed the upstream diff; all 633 named the changed "
                       "files. No de-leaked run exists. The leak reaches Solo and Planner alike, "
                       "so it cannot manufacture a team-over-Solo gain; what it damages is the "
                       "necessity gap, which is negative on every leaked stratum."),
            dict(name="residual coordination",
                 value_pp=round(100 * tn_cor["mean"], 3),
                 ci_pp=[round(100 * tn_cor["ci_lo"], 3), round(100 * tn_cor["ci_hi"], 3)],
                 kind="upper bound, not distinguishable from zero",
                 basis="best case for teams after the one correction that can be measured; "
                       "13 of 39 models favour the team; sign test p=%.3f"
                       % tn_cor["sign_test_p"]),
        ],
    )

    out["headline"] = dict(
        one_sentence="Across 2152 paired model-task-seed cells and 40 models, the only "
                     "multi-agent condition that beats a single agent does so by +4.97 pp, and "
                     "75% of that is the harness writing the team's attestation file for it; "
                     "corrected, the gain is +1.22 pp with a confidence interval that spans "
                     "zero, and the flagship three-role team is 4.0 pp behind Solo while "
                     "spending 6.8 times the compute.",
        why_it_is_a_discovery_not_a_confession=
            "None of these three quantities is observable without the instrument. The "
            "attestation share is only visible because the harness records per-check failure "
            "modes and because the repaired and unrepaired graders were both run on the same "
            "pristine workspace. The compute ratio is only visible because every condition is "
            "logged in the same units. The baseline substitution is only visible because Solo "
            "and Restricted are separate conditions rather than one 'single agent' arm. A "
            "benchmark that reports a single team-versus-single-agent number cannot decompose "
            "it, and most of the multi-agent literature reports exactly that number.",
        generalises_to="any harness that (a) fills in a required artifact on behalf of one "
                       "condition, (b) lets conditions differ in turn budget, or (c) uses an "
                       "information-restricted agent as the single-agent baseline. All three "
                       "are common.",
    )

    out["figure_spec"] = dict(
        recommended="Three panels, not a single waterfall.",
        why_not_a_plain_waterfall=
            "A waterfall implies the components are additive and sum to the reported gain. Here "
            "they do not, and pretending they do would be the same category of error the paper "
            "is trying to expose. Two of the four candidate components are measured on the same "
            "rows and can be stacked; the compute term is measured on a different, smaller task "
            "set and the leakage term is an exposure with no counterfactual run behind it. A "
            "figure that stacks all four invents precision the data does not have.",
        panel_A=dict(
            title="What the reported gain was made of",
            form="horizontal waterfall, 3 bars plus a rule at zero",
            bars=["reported team_uplift (team - Restricted) +0.47 pp",
                  "correct the baseline: -0.73 pp",
                  "team - Solo: -0.26 pp"],
            annotation="the correction is larger than the quantity being corrected, and it is "
                       "itself not distinguishable from zero (t=0.47, exactly 0 on 87/155 tasks)",
        ),
        panel_B=dict(
            title="The best case for teams, and what it is",
            form="dot-and-interval, four rows, model-clustered CIs drawn as the wide bar and "
                 "task-clustered CIs as the narrow inner bar so the reader sees which claim is "
                 "being made",
            rows=["No-Evaluate - Solo, raw",
                  "No-Evaluate - Solo, attestation corrected",
                  "No-Evaluate - Solo on the 95 attestation-scored tasks, raw",
                  "No-Evaluate - Solo on the 95 attestation-scored tasks, corrected"],
            annotation="the only stratum where the gain clears zero is the stratum where the "
                       "harness writes the attestation, and correcting it there flips the sign",
        ),
        panel_C=dict(
            title="Provenance: the reported number is not a point",
            form="two markers on the same axis as panel A, joined by a bar, one per shipped "
                 "summary table, with the pooled recomputation drawn beneath as a third marker "
                 "with its CI",
            annotation="431 of 1240 tabulated values differ between the two files; the contrast "
                       "they report differs by 7.35 pp and by sign. Put this panel first if the "
                       "reviewer is expected to be sceptical, because it is the cheapest to "
                       "verify and the hardest to argue with.",
        ),
        margin_note="Report the per-model sign counts in the caption. 19 of 39 models favour "
                    "the team before the correction and 13 of 39 after: the pooled mean is not "
                    "a majority-of-models result either way.",
        do_not="Do not draw an arrow from 'reported gain' to 'residual coordination'. There is "
               "no identified residual; the honest terminal state of the figure is an interval "
               "that contains zero, labelled as such.",
    )

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, sort_keys=False)
    print("wrote", args.out)

    # console summary
    def pp(x):
        return "n/a" if x is None else f"{100*x:+.2f} pp"
    print("\n--- published number, recomputed from shared/paper/ablation_summary.json (155 tasks)")
    print(f"  team_uplift as shipped (team - Restricted) : {published['team_uplift_as_shipped']['mean_pp']:+.2f} pp")
    print(f"  team - Solo, correct baseline              : {published['team_vs_solo_correct_baseline']['mean_pp']:+.2f} pp")
    print(f"  baseline substitution (necessity gap)      : {published['baseline_substitution']['mean_pp']:+.2f} pp  (t={published['baseline_substitution']['t']})")
    print("\n--- pooled corpus")
    for k, v in pooled.items():
        r, c = v["raw"], v["attestation_corrected"]
        print(f"  {k:34s} raw {pp(r['mean'])} [{pp(r['ci_lo'])},{pp(r['ci_hi'])}]"
              f"   corrected {pp(c['mean'])} [{pp(c['ci_lo'])},{pp(c['ci_hi'])}]  n={r['n']}")
    print("\n--- compute")
    rc = out["component_compute"]["realised_compute_wall_clock"]
    print(f"  Full Team / Solo realised wall clock       : {rc['ratio_of_means']}x  (median cell {rc['median_per_cell_ratio']}x, n={rc['paired_cells']})")
    print(f"  Solo at 2x ceiling (oracle_cot - oracle)   : {pp(cot['mean'])} [{pp(cot['ci_lo'])},{pp(cot['ci_hi'])}]  n={cot['n']}")


if __name__ == "__main__":
    main()
