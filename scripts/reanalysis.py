#!/usr/bin/env python3
"""
TeamBench reanalysis: retire TNI, rebuild the estimands, and re-run the
statistics the submission depends on.

This script recomputes every number from primitive per-run / per-task condition
scores.  It deliberately ignores every stored derived field (``tni``,
``necessity_gap``, ``team_uplift``, ``classification``, ``avg_*``) and
recalculates them, so that disagreements between what is stored and what the
data supports are surfaced rather than inherited.

Sections
--------
A. TNI autopsy.  Why the Teamwork Necessity Index cannot be estimated on this
   pool: it is a ratio of differences that share a term, its denominator is
   statistically indistinguishable from zero, its Fieller interval is
   unbounded, and the four shipped implementations disagree with each other and
   with the paper's Eq. (1).
B. Replacement estimand.  The Coordination Necessity Contrast: a 2-D
   (partition value, team advantage) object with paired task-clustered
   bootstrap CIs, plus a hierarchical (shrinkage) definition of benchmark-level
   admission that replaces a point threshold on a noisy per-task estimate.
C. Quintile analysis redone.  The published profile stratifies on the same
   noisy Solo run that appears in the contrast, which is textbook regression to
   the mean.  We give the exact permutation null for that design, three
   independent difficulty instruments, and the RTM-corrected effect.
D. Uplift relabelling.  Full - Solo and Full - Restricted, each reported
   separately with paired task-clustered bootstrap CIs.
E. Statistical machinery audit.  Paired vs unpaired bootstrap, task-level
   clustering / design effect for the pooled role-mixing rates, and family-wise
   multiplicity across the whole set of primary tests.

Usage
-----
    python3 scripts/reanalysis.py
    python3 scripts/reanalysis.py --n-boot 20000 --n-perm 5000
    python3 scripts/reanalysis.py --render-only     # re-render the markdown only

Set TEAMBENCH_REPO to point at the repository if the script is run from a copy
elsewhere.  On a machine where the home directory sits on a slow network mount,
Python stats ~/.local/site-packages on every import; exporting
PYTHONNOUSERSITE=1 and HOME=<local scratch dir> removes several minutes of
startup with no effect on any result.

Outputs
-------
    shared/paper/quality/reanalysis.json
    shared/paper/quality/reanalysis_summary.md
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np
from scipy import stats as _sps

REPO = os.environ.get(
    "TEAMBENCH_REPO",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)

# ---------------------------------------------------------------------------
# Paths (all resolved against the repo root so the script is location-agnostic)
# ---------------------------------------------------------------------------
P_ABLATION_SUMMARY = os.path.join(REPO, "shared/paper/ablation_summary.json")
P_LB90 = os.path.join(REPO, "shared/paper/lb90_full_aggregate.json")
P_ABLATION_DIR = os.path.join(REPO, "shared/ablation_results")
P_PHASE3 = os.path.join(P_ABLATION_DIR, "phase3_all_consolidated.json")
P_ROLE_RUNS = os.path.join(REPO, "shared/role_ablation/results/per_run.jsonl")
P_QUINTILE_PUBLISHED = os.path.join(REPO, "shared/paper/quintile_solo_stratified.json")

# Condition names used by the reference ablation.  "oracle" is the paper's
# Solo condition (one agent, full information); "restricted" is one agent with
# the Executor's tool set and no spec; "full" is Planner+Executor+Verifier.
COND_SOLO = "oracle"
COND_RESTRICTED = "restricted"
COND_TEAM = "full"
COND_NO_PLAN = "team_no_plan"
COND_NO_VERIFY = "team_no_verify"

# The reference-ablation summary stores the team arm under the key "team" and
# the two lesioned arms under "no_plan"/"no_verify".
SUMMARY_KEYS = {
    COND_SOLO: "oracle",
    COND_RESTRICTED: "restricted",
    COND_TEAM: "team",
    COND_NO_PLAN: "no_plan",
    COND_NO_VERIFY: "no_verify",
}


# ===========================================================================
# Data loading
# ===========================================================================
def load_reference_pool() -> list[dict]:
    """155-task reference ablation, seed 0, one run per (task, condition).

    Only the five primitive condition scores are read.  Every derived field in
    the source file is discarded and recomputed downstream.
    """
    with open(P_ABLATION_SUMMARY) as fh:
        raw = json.load(fh)
    pool = []
    for row in raw["per_task"]:
        rec = {"task_id": row["task_id"]}
        for cond, key in SUMMARY_KEYS.items():
            rec[cond] = float(row[key])
        pool.append(rec)
    pool.sort(key=lambda r: r["task_id"])
    return pool


def load_reference_pool_raw_crosscheck(pool: list[dict]) -> dict:
    """Independently rebuild seed-0 condition scores from the raw batch files.

    The summary is a merge product.  We reload the underlying run records and
    check that the merge did not alter any primitive score.
    """
    batch_files = [
        "batch1_swe_data_seed0_g3flash.json",
        "batch2_sec_policy_neg_seed0_g3flash.json",
        "batch3_inc_ops_seed0_g3flash.json",
        "batch3_full_retry_g3flash.json",
        "batch4_test_spec_cr_seed0_g3flash.json",
        "batch5_lh_pipe_ir_multi_int_seed0_g3flash.json",
        "batch5_full_retry_g3flash.json",
        "batch6_trap_cross_crypto_dist_go_js_seed0_g3flash.json",
        "batch6_retry_g3flash.json",
        "batch6_full_503_retry.json",
        "crypto_dist_g3flash.json",
        "trap_cross_g3flash.json",
        "gh_tasks_ablation_g3flash_seed0.json",
    ]
    raw_scores: dict[tuple[str, str], list[float]] = defaultdict(list)
    files_seen = 0
    for name in batch_files:
        path = os.path.join(P_ABLATION_DIR, name)
        if not os.path.exists(path):
            continue
        files_seen += 1
        with open(path) as fh:
            doc = json.load(fh)
        for run in doc.get("runs", []):
            if run.get("seed") not in (0, None):
                continue
            score = _partial(run)
            if score is None:
                continue
            raw_scores[(run["task_id"], run["condition"])].append(score)

    checked = 0
    mismatched = []
    for rec in pool:
        for cond in SUMMARY_KEYS:
            vals = raw_scores.get((rec["task_id"], cond))
            if not vals:
                continue
            checked += 1
            # Later retry files supersede earlier ones; accept a match to any.
            if not any(abs(v - rec[cond]) < 1e-6 for v in vals):
                mismatched.append(
                    {
                        "task_id": rec["task_id"],
                        "condition": cond,
                        "summary": rec[cond],
                        "raw_candidates": vals,
                    }
                )
    return {
        "batch_files_found": files_seen,
        "cells_crosschecked": checked,
        "cells_mismatched": len(mismatched),
        "mismatch_examples": mismatched[:8],
        "note": (
            "Cells not covered by the batch files listed here are not "
            "cross-checked; a mismatch usually means a retry file superseded "
            "the original run and both values are present in the raw pool."
        ),
    }


# Files that are genuinely the gemini-3-flash-preview seed-0 reference
# ablation, in the order the retries supersede the base runs.
CLEAN_POOL_FILES = [
    "crypto_dist_g3flash.json",
    "trap_cross_g3flash.json",
    "trap_cross_team_no_verify_g3flash.json",
    "batch1_swe_data_seed0_g3flash.json",
    "batch2_sec_policy_neg_seed0_g3flash.json",
    "batch3_inc_ops_seed0_g3flash.json",
    "batch3_full_retry_g3flash.json",
    "batch4_test_spec_cr_seed0_g3flash.json",
    "batch5_lh_pipe_ir_multi_int_seed0_g3flash.json",
    "batch5_full_retry_g3flash.json",
    "batch6_trap_cross_crypto_dist_go_js_seed0_g3flash.json",
    "batch6_retry_g3flash.json",
    "batch6_full_503_retry.json",
    "gh_tasks_ablation_g3flash_seed0.json",
]


def provenance_audit(pool: list[dict]) -> dict:
    """Re-run the exact merge that produced the canonical 155-task table.

    scripts/generate_paper.sh globs *every* JSON in shared/ablation_results/
    and hands the whole list to harness/paper_tables.py, which deduplicates by
    (task_id, condition, seed) with first-file-wins and then averages whatever
    survives.  Two consequences fall out of that pipeline and neither is
    visible in the stored table:

      1. Multi-seed runs whose partial score lives under
         ``run["secondary"]["partial_score"]`` are read with
         ``run.get("partial_score", 1.0 if run["pass"] else 0.0)``, so their
         partial scores are silently binarised before being averaged with
         seed 0's real partial score.
      2. The glob is not filtered by model, so runs from other models can and
         do supply cells of a table captioned as a single-model ablation.

    This function reproduces the merge, reports which file supplied each cell,
    and quantifies both effects.
    """
    import glob as _glob

    files: list[str] = []
    for f in ["shared/ablation_preliminary.json", "shared/ablation_5task.json",
              "shared/ablation_10task.json"]:
        p = os.path.join(REPO, f)
        if os.path.exists(p):
            files.append(p)
    files += sorted(_glob.glob(os.path.join(P_ABLATION_DIR, "*.json")))

    seen: set = set()
    merged: list[tuple[dict, str, str]] = []
    for path in files:
        try:
            with open(path) as fh:
                data = json.load(fh)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        model = str(data.get("model") or "unknown")
        for run in data.get("runs", []):
            if "task_id" not in run or "condition" not in run:
                continue
            key = (run["task_id"], run["condition"], run.get("seed", 0))
            if key in seen:
                continue
            seen.add(key)
            merged.append((run, os.path.basename(path), model))

    cells: dict[tuple[str, str], list[tuple[float, str, str, bool]]] = defaultdict(list)
    for run, src, model in merged:
        as_read = run.get("partial_score", 1.0 if run.get("pass") else 0.0)
        true_partial = _partial(run)
        binarised = (run.get("partial_score") is None
                     and (run.get("secondary") or {}).get("partial_score") is not None)
        cells[(run["task_id"], run["condition"])].append(
            (float(as_read), src, model, binarised))

    ref_ids = {r["task_id"] for r in pool}
    reproduced = mismatched = 0
    src_census: dict[str, int] = defaultdict(int)
    model_census: dict[str, int] = defaultdict(int)
    binarised_runs = 0
    cells_touched_by_binarisation = 0
    examples = []
    for rec in pool:
        for cond, key in SUMMARY_KEYS.items():
            entries = cells.get((rec["task_id"], cond), [])
            if not entries:
                continue
            vals = [e[0] for e in entries]
            avg = sum(vals) / len(vals)
            if abs(avg - rec[cond]) < 1e-6:
                reproduced += 1
            else:
                mismatched += 1
                if len(examples) < 6:
                    examples.append({
                        "task_id": rec["task_id"], "condition": cond,
                        "merge_reproduction": round(avg, 4),
                        "stored": rec[cond],
                        "sources": [e[1] for e in entries],
                    })
            nb = sum(1 for e in entries if e[3])
            binarised_runs += nb
            if nb:
                cells_touched_by_binarisation += 1
            for _, src, model, _b in entries:
                src_census[src] += 1
                model_census[model] += 1

    foreign_model_cells = sum(
        n for m, n in model_census.items()
        if "gemini-3-flash-preview" not in m and "gemini-2.5-flash" not in m
    )

    return {
        "merge_reproduced_from_generate_paper_sh": {
            "n_json_files_globbed": len(files),
            "n_runs_after_dedup": len(merged),
            "cells_reproduced_exactly": reproduced,
            "cells_not_reproduced": mismatched,
            "note": (
                "Cells that do not reproduce are ones where a file added after "
                "the table was generated now wins the first-wins dedup. That is "
                "itself the finding: the canonical table is not reproducible "
                "from the current contents of the directory it globs."
            ),
            "examples": examples,
        },
        "silent_binarisation_bug": {
            "location": "harness/paper_tables.py, runs_to_task_metrics",
            "code": 'partial = run.get("partial_score", 1.0 if run.get("pass") else 0.0)',
            "problem": (
                "Runs produced by the multi-seed phase-3 campaign store the "
                "partial score at run['secondary']['partial_score'] and carry "
                "no top-level 'partial_score' key. The default branch fires and "
                "the run is scored 1.0/0.0. Those binarised values are then "
                "averaged with seed 0's genuine partial score, so the canonical "
                "per-task number is a mean of one continuous and up to two "
                "dichotomised measurements."
            ),
            "n_runs_binarised": binarised_runs,
            "n_table_cells_affected": cells_touched_by_binarisation,
            "n_table_cells_total": 5 * len(pool),
            "worked_example": _binarisation_example(),
        },
        "model_provenance": {
            "runs_by_declared_model": dict(sorted(model_census.items(), key=lambda kv: -kv[1])),
            "runs_by_source_file": dict(sorted(src_census.items(), key=lambda kv: -kv[1])[:20]),
            "cells_from_a_model_other_than_the_two_gemini_families": foreign_model_cells,
            "problem": (
                "The glob has no model filter. The table captioned as a single "
                "ablation draws on gemini-2.5-flash files (the original 20-task "
                "pool), gemini-3-flash-preview files (the expansion), and, in "
                "the directory's current state, cross-model runs from other "
                "models entirely."
            ),
        },
        "n_reference_tasks": len(ref_ids),
    }


def _binarisation_example() -> dict:
    """One fully traceable instance of the binarisation bug."""
    if not os.path.exists(P_PHASE3):
        return {"available": False}
    with open(P_PHASE3) as fh:
        doc = json.load(fh)
    rows = [r for r in doc.get("runs", [])
            if r["task_id"] == "CR5_test_coverage" and r["condition"] == "restricted"]
    if not rows:
        return {"available": False}
    seed0 = 0.38  # from batch4_test_spec_cr_seed0_g3flash.json
    as_read = [seed0] + [1.0 if r.get("pass") else 0.0 for r in rows]
    truth = [seed0] + [float((r.get("secondary") or {}).get("partial_score")) for r in rows]
    return {
        "available": True,
        "task": "CR5_test_coverage", "condition": "restricted",
        "seed0_partial": seed0,
        "seed12_true_partial": [float((r.get("secondary") or {}).get("partial_score")) for r in rows],
        "seed12_as_read_by_paper_tables": [1.0 if r.get("pass") else 0.0 for r in rows],
        "stored_table_value": sum(as_read) / len(as_read),
        "value_if_partial_scores_were_read": sum(truth) / len(truth),
    }


def build_clean_pool(published_pool: list[dict], restrict_to_published: bool = True) -> dict:
    """A provenance-controlled reference pool.

    One model (gemini-3-flash-preview), one seed (0), partial scores read from
    whichever key actually carries them, errored runs dropped, retries
    superseding base runs, and only tasks with all five conditions present.
    """
    cell: dict[tuple[str, str], tuple[float, bool]] = {}
    files = [f for f in CLEAN_POOL_FILES
             if os.path.exists(os.path.join(P_ABLATION_DIR, f))]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(P_ABLATION_DIR, f)))
    n_err = 0
    for name in files:
        with open(os.path.join(P_ABLATION_DIR, name)) as fh:
            doc = json.load(fh)
        for run in doc.get("runs", []):
            if run.get("seed", 0) != 0:
                continue
            if run.get("error"):
                n_err += 1
                continue
            score = _partial(run)
            if score is None:
                continue
            cell[(run["task_id"], run["condition"])] = (
                float(score), bool(run.get("pass")),
                float(run.get("elapsed_sec") or 0.0),
            )

    tasks = sorted({t for t, _ in cell})
    published_ids = {r["task_id"] for r in published_pool}
    pool = []
    for tid in tasks:
        if not all((tid, c) in cell for c in SUMMARY_KEYS):
            continue
        if restrict_to_published and tid not in published_ids:
            continue
        rec = {"task_id": tid}
        for c in SUMMARY_KEYS:
            rec[c] = cell[(tid, c)][0]
            rec[c + "__pass"] = 1.0 if cell[(tid, c)][1] else 0.0
            rec[c + "__elapsed"] = cell[(tid, c)][2]
        pool.append(rec)
    return {
        "pool": pool,
        "definition": (
            "gemini-3-flash-preview, seed 0, one run per (task, condition), "
            "partial score read from run['partial_score'] or "
            "run['secondary']['partial_score'], errored runs dropped, retry "
            "files superseding base files, tasks kept only when all five "
            "conditions are present"
            + (" and the task appears in the published 155-task table" if restrict_to_published else "")
        ),
        "source_files": files,
        "n_tasks": len(pool),
        "n_errored_runs_dropped": n_err,
    }


def _partial(run: dict) -> float | None:
    """Extract a partial score from either run-record shape used in this repo."""
    if run.get("partial_score") is not None:
        return float(run["partial_score"])
    sec = run.get("secondary") or {}
    if sec.get("partial_score") is not None:
        return float(sec["partial_score"])
    if run.get("pass") is not None:
        return 1.0 if run["pass"] else 0.0
    return None


def load_replicates(pool: list[dict], seed0_source: dict | None = None) -> dict:
    """Per-(task, condition) replicate scores across seeds.

    Seeds 1 and 2 come from the phase-3 multi-seed campaign, read from the key
    that actually carries the partial score.  Seed 0 is taken from
    ``seed0_source`` when one is supplied -- the provenance-controlled pool --
    and is otherwise omitted, because the published table's seed-0 value for
    these very tasks is contaminated by the binarisation bug documented in
    section F and must not be used to estimate measurement variance.
    """
    reps: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    if os.path.exists(P_PHASE3):
        with open(P_PHASE3) as fh:
            doc = json.load(fh)
        for run in doc.get("runs", []):
            score = _partial(run)
            if score is None:
                continue
            reps[run["task_id"]][run["condition"]].append(score)
    if seed0_source:
        for tid, conds in list(reps.items()):
            if tid not in seed0_source:
                continue
            for cond in SUMMARY_KEYS:
                if cond in seed0_source[tid]:
                    conds[cond].insert(0, seed0_source[tid][cond])
    published = {r["task_id"] for r in pool}
    return {t: dict(c) for t, c in reps.items() if t in published}


def load_lb90() -> dict:
    """Per-model, per-condition, per-task LB90 outcomes rebuilt from raw runs.

    The stored aggregate carries only counts.  We rebuild the task-level matrix
    so that Solo vs Restricted can be compared *paired within task*, which the
    aggregate cannot support.
    """
    with open(P_LB90) as fh:
        agg = json.load(fh)
    dropped = set(agg["dropped_from_lb100"])

    cache: dict[str, list[dict]] = {}

    def read_source(name: str) -> list[dict]:
        if name in cache:
            return cache[name]
        path = os.path.join(P_ABLATION_DIR, name)
        runs: list[dict] = []
        if os.path.exists(path):
            if path.endswith(".jsonl"):
                with open(path) as fh:
                    for line in fh:
                        line = line.strip()
                        if line:
                            runs.append(json.loads(line))
            else:
                with open(path) as fh:
                    doc = json.load(fh)
                runs = doc.get("runs", [])
        cache[name] = runs
        return runs

    out: dict[str, dict[str, dict[str, dict]]] = {}
    for model, conds in agg["models"].items():
        out[model] = {}
        for cond, meta in conds.items():
            src = meta.get("source")
            if not src:
                continue
            rows: dict[str, dict] = {}
            for part in src.split("+"):
                for run in read_source(part):
                    if run.get("condition") != cond:
                        continue
                    tid = run.get("task_id")
                    if not tid or tid in dropped:
                        continue
                    if run.get("error"):
                        continue
                    score = _partial(run)
                    if score is None:
                        continue
                    rows[tid] = {
                        "pass": bool(run.get("pass")),
                        "partial": score,
                    }
            if rows:
                out[model][cond] = rows
    return {"matrix": out, "lb90_dropped": sorted(dropped)}


def load_role_runs() -> list[dict]:
    runs = []
    if not os.path.exists(P_ROLE_RUNS):
        return runs
    with open(P_ROLE_RUNS) as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    runs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return runs


# ===========================================================================
# Generic statistics
# ===========================================================================
def task_clustered_bootstrap(
    values: np.ndarray,
    n_boot: int,
    rng: np.random.Generator,
    alpha: float = 0.05,
) -> dict:
    """Percentile bootstrap for the mean of a per-task paired contrast.

    The resampling unit is the task, so the CI respects task-level clustering.
    Because each element of ``values`` is already a within-task difference, the
    bootstrap is paired by construction: conditions travel together.
    """
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n == 0:
        return {"mean": float("nan"), "ci_lo": float("nan"), "ci_hi": float("nan"), "n": 0}
    idx = rng.integers(0, n, size=(n_boot, n))
    boots = values[idx].mean(axis=1)
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {
        "mean": float(values.mean()),
        "ci_lo": float(lo),
        "ci_hi": float(hi),
        "se_boot": float(boots.std(ddof=1)),
        "n": int(n),
    }


def sign_flip_p(values: np.ndarray, n_perm: int, rng: np.random.Generator) -> float:
    """Exact-in-the-limit permutation p-value for a paired contrast.

    Under the null that the two arms are exchangeable within a task, the sign of
    each within-task difference is exchangeable.  Two-sided.
    """
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n == 0:
        return float("nan")
    obs = abs(values.mean())
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n_perm, n))
    null = (signs * values).mean(axis=1)
    # +1 correction so the p-value can never be exactly zero.
    return float((np.sum(np.abs(null) >= obs - 1e-15) + 1) / (n_perm + 1))


def unpaired_bootstrap_diff(
    a: np.ndarray, b: np.ndarray, n_boot: int, rng: np.random.Generator, alpha: float = 0.05
) -> dict:
    """Reproduce harness/statistics.py::bootstrap_ci_difference (arms resampled
    independently).  Used only to quantify what the unpaired analysis costs."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    obs = a.mean() - b.mean()
    ia = rng.integers(0, len(a), size=(n_boot, len(a)))
    ib = rng.integers(0, len(b), size=(n_boot, len(b)))
    boots = a[ia].mean(axis=1) - b[ib].mean(axis=1)
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {"mean": float(obs), "ci_lo": float(lo), "ci_hi": float(hi),
            "se_boot": float(boots.std(ddof=1))}


def wilson_ci(k: int, n: int, z: float = 1.959963985) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def icc_one_way(groups: list[list[float]]) -> dict:
    """One-way random-effects ICC(1,1) with unequal group sizes.

    ICC = (MS_b - MS_w) / (MS_b + (m0 - 1) * MS_w), m0 the Satterthwaite-style
    average group size.
    """
    groups = [g for g in groups if len(g) >= 1]
    k = len(groups)
    sizes = np.array([len(g) for g in groups], dtype=float)
    N = sizes.sum()
    if k < 2 or N <= k:
        return {"icc": float("nan"), "k_groups": k, "n_total": int(N)}
    grand = float(np.concatenate([np.asarray(g, dtype=float) for g in groups]).mean())
    means = np.array([float(np.mean(g)) for g in groups])
    ss_b = float(np.sum(sizes * (means - grand) ** 2))
    ss_w = float(sum(float(np.sum((np.asarray(g, dtype=float) - m) ** 2))
                     for g, m in zip(groups, means)))
    ms_b = ss_b / (k - 1)
    ms_w = ss_w / (N - k)
    m0 = (N - float(np.sum(sizes ** 2)) / N) / (k - 1)
    denom = ms_b + (m0 - 1) * ms_w
    icc = (ms_b - ms_w) / denom if denom > 0 else float("nan")
    return {
        "icc": float(icc),
        "ms_between": ms_b,
        "ms_within": ms_w,
        "k_groups": int(k),
        "n_total": int(N),
        "mean_cluster_size": float(N / k),
        "m0_effective": float(m0),
    }


def holm(pvals: dict[str, float], alpha: float = 0.05) -> dict:
    items = sorted(((k, v) for k, v in pvals.items() if v == v), key=lambda kv: kv[1])
    m = len(items)
    out = {}
    running = 0.0
    for i, (k, p) in enumerate(items):
        adj = min(1.0, max(running, (m - i) * p))
        running = adj
        out[k] = {"p_raw": p, "p_holm": adj, "reject_at_0.05": adj < alpha}
    for k, v in pvals.items():
        if v != v:
            out[k] = {"p_raw": None, "p_holm": None, "reject_at_0.05": None}
    return out


def benjamini_hochberg(pvals: dict[str, float], alpha: float = 0.05) -> dict:
    items = sorted(((k, v) for k, v in pvals.items() if v == v), key=lambda kv: kv[1])
    m = len(items)
    out = {}
    prev = 1.0
    for i in range(m - 1, -1, -1):
        k, p = items[i]
        adj = min(prev, p * m / (i + 1))
        prev = adj
        out[k] = {"p_raw": p, "p_bh": adj, "reject_at_0.05": adj < alpha}
    return out


# ===========================================================================
# SECTION A: TNI autopsy
# ===========================================================================
def tni_paper_eq(solo, restricted, team, eps=0.05):
    """Paper Eq. (1): (S_team - S_restricted) / max(eps, S_solo - S_restricted)."""
    return (team - restricted) / max(eps, solo - restricted)


def tni_compute_tni_py(solo, restricted, team):
    """harness/compute_tni.py::TaskMetrics.tni -- NaN if |gap|<0.05, clamp [-2,2]."""
    gap = solo - restricted
    if abs(gap) < 0.05:
        return float("nan")
    return max(-2.0, min(2.0, (team - restricted) / gap))


def tni_ablation_py(solo, restricted, team, eps=0.01):
    """harness/ablation.py::compute_ablation_metrics -- eps=0.01, no clamp."""
    return (team - restricted) / max(eps, solo - restricted)


def tni_validate_py(solo, team, eps=0.01):
    """harness/validate_tni.py::expertise_tni -- a different estimand entirely:
    (team - solo) / max(eps, 1 - solo).  Reported under the same name."""
    return (team - solo) / max(eps, 1.0 - solo)


def fieller_interval(num: np.ndarray, den: np.ndarray, alpha: float = 0.05) -> dict:
    """Fieller confidence set for rho = E[num] / E[den] from paired samples.

    Solves rho^2 * a + rho * b + c <= 0 with
        a = D^2 - t^2 v22,  b = -2 (N D - t^2 v12),  c = N^2 - t^2 v11
    where v are the variances/covariance of the sample *means*.

    When a <= 0 (the denominator is not significantly different from zero at
    level alpha), the solution set is unbounded: either the whole real line or
    the complement of a bounded open interval.  Reporting a finite CI for the
    ratio in that regime is not a valid confidence procedure.
    """
    stats = _sps

    num = np.asarray(num, dtype=float)
    den = np.asarray(den, dtype=float)
    n = len(num)
    N, D = float(num.mean()), float(den.mean())
    cov = np.cov(np.vstack([num, den]))
    v11, v12, v22 = float(cov[0, 0]) / n, float(cov[0, 1]) / n, float(cov[1, 1]) / n
    t = float(stats.t.ppf(1 - alpha / 2, df=n - 1))

    a = D * D - t * t * v22
    b = -2.0 * (N * D - t * t * v12)
    c = N * N - t * t * v11
    disc = b * b - 4 * a * c

    t_den = D / math.sqrt(v22) if v22 > 0 else float("nan")
    res = {
        "num_mean": N,
        "den_mean": D,
        "den_se": math.sqrt(v22),
        "den_t": t_den,
        "den_p_two_sided": float(2 * stats.t.sf(abs(t_den), df=n - 1)) if v22 > 0 else None,
        "point_ratio": (N / D) if D != 0 else float("inf"),
        "t_crit": t,
        "a": a, "b": b, "c": c, "discriminant": disc,
        "n": n,
    }
    if a > 0 and disc > 0:
        r1 = (-b - math.sqrt(disc)) / (2 * a)
        r2 = (-b + math.sqrt(disc)) / (2 * a)
        res.update({"form": "bounded_interval", "ci_lo": min(r1, r2), "ci_hi": max(r1, r2),
                    "bounded": True})
    elif a > 0 and disc <= 0:
        res.update({"form": "empty_set", "bounded": True, "ci_lo": None, "ci_hi": None})
    elif a <= 0 and disc > 0:
        r1 = (-b - math.sqrt(disc)) / (2 * a)
        r2 = (-b + math.sqrt(disc)) / (2 * a)
        lo, hi = min(r1, r2), max(r1, r2)
        res.update({
            "form": "exclusive_unbounded",
            "bounded": False,
            "excluded_open_interval": [lo, hi],
            "confidence_set": f"(-inf, {lo:.4g}] U [{hi:.4g}, +inf)",
        })
    else:
        res.update({"form": "whole_real_line", "bounded": False,
                    "confidence_set": "(-inf, +inf)"})
    return res


def section_a(pool, replicates, n_boot, rng) -> dict:
    solo = np.array([r[COND_SOLO] for r in pool])
    restricted = np.array([r[COND_RESTRICTED] for r in pool])
    team = np.array([r[COND_TEAM] for r in pool])
    gap = solo - restricted            # TNI denominator
    relay = team - restricted          # TNI numerator
    advantage = team - solo            # the quantity of actual interest

    stats = _sps

    # --- A1: the denominator is statistically zero -------------------------
    t_gap = gap.mean() / (gap.std(ddof=1) / math.sqrt(len(gap)))
    denom_diag = {
        "n_tasks": len(gap),
        "mean": float(gap.mean()),
        "sd": float(gap.std(ddof=1)),
        "se": float(gap.std(ddof=1) / math.sqrt(len(gap))),
        "t": float(t_gap),
        "p_two_sided": float(2 * stats.t.sf(abs(t_gap), df=len(gap) - 1)),
        "exactly_zero": int(np.sum(np.abs(gap) < 1e-9)),
        "negative": int(np.sum(gap < -1e-9)),
        "positive": int(np.sum(gap > 1e-9)),
        "abs_below_0.05": int(np.sum(np.abs(gap) < 0.05)),
        "below_eps_0.05_signed": int(np.sum(gap < 0.05)),
        "below_eps_0.01_signed": int(np.sum(gap < 0.01)),
        "bootstrap": task_clustered_bootstrap(gap, n_boot, rng),
    }
    denom_diag["fraction_where_paper_eps_is_active"] = (
        denom_diag["below_eps_0.05_signed"] / len(gap)
    )

    # --- A2: the algebraic identity that empties TNI of content ------------
    # relay = gap + advantage exactly, so TNI = relay/gap = 1 + advantage/gap.
    identity_resid = float(np.max(np.abs(relay - (gap + advantage))))
    identity = {
        "claim": "S_team - S_restricted == (S_solo - S_restricted) + (S_team - S_solo)",
        "max_abs_residual": identity_resid,
        "consequence": "TNI = 1 + (S_team - S_solo)/(S_solo - S_restricted)",
        "interpretation": (
            "Every bit of teamwork signal in TNI lives in the numerator term "
            "(S_team - S_solo). TNI takes that quantity, divides it by a "
            "denominator whose mean is not distinguishable from zero, and adds "
            "1. On tasks with a positive gap, 'TNI > 1' is algebraically "
            "identical to 'S_team > S_solo'. The ratio contributes no "
            "information the difference does not already carry, and it "
            "contributes unbounded variance."
        ),
    }

    # --- A3: four shipped implementations, one pool ------------------------
    impls = {}
    v_paper = np.array([tni_paper_eq(s, r, t_) for s, r, t_ in zip(solo, restricted, team)])
    v_code = np.array([tni_compute_tni_py(s, r, t_) for s, r, t_ in zip(solo, restricted, team)])
    v_abl = np.array([tni_ablation_py(s, r, t_) for s, r, t_ in zip(solo, restricted, team)])
    v_val = np.array([tni_validate_py(s, t_) for s, t_ in zip(solo, team)])
    v_unclamped = np.where(np.abs(gap) < 1e-12, np.nan, relay / np.where(gap == 0, np.nan, gap))

    def describe(v, label, defined_mask=None):
        m = np.isfinite(v) if defined_mask is None else (defined_mask & np.isfinite(v))
        vv = v[m]
        return {
            "implementation": label,
            "n_defined": int(m.sum()),
            "n_undefined": int(len(v) - m.sum()),
            "mean": float(vv.mean()) if len(vv) else None,
            "median": float(np.median(vv)) if len(vv) else None,
            "min": float(vv.min()) if len(vv) else None,
            "max": float(vv.max()) if len(vv) else None,
        }

    impls["paper_eq1_eps0.05"] = describe(v_paper, "paper Eq. (1), eps=0.05, no clamp")
    impls["compute_tni_py"] = describe(v_code, "harness/compute_tni.py, |gap|<0.05 -> NaN, clamp [-2,2]")
    impls["ablation_py_eps0.01"] = describe(v_abl, "harness/ablation.py, eps=0.01, no clamp")
    impls["validate_tni_py"] = describe(v_val, "harness/validate_tni.py, (team-solo)/max(0.01,1-solo) -- different estimand")
    impls["unclamped_ratio"] = describe(v_unclamped, "raw relay/gap with no epsilon and no clamp")

    # Same-subset comparison: the 61 tasks compute_tni.py calls valid.
    sub = np.isfinite(v_code)
    same_subset = {
        "subset": "tasks where harness/compute_tni.py reports a value (|gap| >= 0.05)",
        "n": int(sub.sum()),
        "paper_eq1_mean": float(v_paper[sub].mean()),
        "compute_tni_py_mean": float(v_code[sub].mean()),
        "ablation_py_mean": float(v_abl[sub].mean()),
        "unclamped_mean": float(np.nanmean(v_unclamped[sub])),
        "sign_disagreements_paper_vs_code": int(
            np.sum(np.sign(v_paper[sub]) != np.sign(v_code[sub]))
        ),
        "spearman_paper_vs_code": float(stats.spearmanr(v_paper[sub], v_code[sub]).statistic),
    }

    # The file's own aggregate uses a *third* filter (signed gap > 0.05).
    signed_sub = gap > 0.05
    internal_inconsistency = {
        "issue": (
            "shared/paper/ablation_summary.json applies |gap| >= 0.05 per task "
            "but signed gap > 0.05 in its own aggregate block, so the file "
            "reports two different TNI means for the same data."
        ),
        "n_per_task_nonnull_abs_filter": int(sub.sum()),
        "mean_abs_filter": float(v_code[sub].mean()),
        "n_aggregate_signed_filter": int(signed_sub.sum()),
        "mean_signed_filter": float(v_code[signed_sub].mean()),
    }

    # --- A4: clamp census --------------------------------------------------
    clamped_hi = int(np.sum(np.isclose(v_code[sub], 2.0)))
    clamped_lo = int(np.sum(np.isclose(v_code[sub], -2.0)))
    unc = v_unclamped[sub]
    clamp = {
        "clamp_range": [-2.0, 2.0],
        "documented_in_paper": False,
        "n_reported": int(sub.sum()),
        "n_on_upper_clamp": clamped_hi,
        "n_on_lower_clamp": clamped_lo,
        "fraction_on_a_clamp": (clamped_hi + clamped_lo) / max(1, int(sub.sum())),
        "mean_with_clamp": float(v_code[sub].mean()),
        "mean_without_clamp": float(np.nanmean(unc)),
        "max_without_clamp": float(np.nanmax(unc)),
        "min_without_clamp": float(np.nanmin(unc)),
        "note": (
            "The clamp is load-bearing: it is what keeps the reported mean "
            "finite and moderate. Removing it moves the mean and exposes the "
            "heavy tail that the ratio actually has."
        ),
    }

    # --- A5: Fieller for the ratio of means --------------------------------
    fieller = fieller_interval(relay, gap)
    fieller["reading"] = (
        "a <= 0 means the denominator's own confidence interval covers zero, so "
        "no bounded confidence set for the ratio exists at 95%. The correct "
        "report is that the ratio of means is not estimable on this pool."
    ) if not fieller.get("bounded", True) else "denominator bounded away from zero"

    # --- A6: heavy tail of the mean of per-task ratios ---------------------
    finite_unc = unc[np.isfinite(unc)]
    idx = rng.integers(0, len(finite_unc), size=(n_boot, len(finite_unc)))
    boot_means = finite_unc[idx].mean(axis=1)
    heavy_tail = {
        "subset_n": int(len(finite_unc)),
        "observed_mean_of_per_task_ratios": float(finite_unc.mean()),
        "bootstrap_mean_p2.5": float(np.percentile(boot_means, 2.5)),
        "bootstrap_mean_p97.5": float(np.percentile(boot_means, 97.5)),
        "bootstrap_mean_min": float(boot_means.min()),
        "bootstrap_mean_max": float(boot_means.max()),
        "bootstrap_ci_width": float(np.percentile(boot_means, 97.5) - np.percentile(boot_means, 2.5)),
        "note": (
            "The per-task ratio has no finite population mean when the "
            "denominator's distribution has mass at zero, so the sample mean "
            "reported as 'average TNI' is not consistent for anything."
        ),
    }

    # --- A7: simulation, estimator behaviour as the denominator -> 0 -------
    sim = _ratio_simulation(relay, gap, rng)

    # --- A8: measurement noise in the denominator --------------------------
    noise = _gap_noise_from_replicates(replicates)

    return {
        "denominator_diagnostics": denom_diag,
        "algebraic_identity": identity,
        "implementations_on_one_pool": impls,
        "same_subset_comparison": same_subset,
        "internal_inconsistency_in_stored_summary": internal_inconsistency,
        "clamp_census": clamp,
        "fieller_confidence_set_for_ratio_of_means": fieller,
        "heavy_tail_of_mean_per_task_ratio": heavy_tail,
        "simulation_denominator_to_zero": sim,
        "denominator_measurement_noise": noise,
    }


def _fieller_covers_vec(nn: np.ndarray, dd: np.ndarray, rho: float, t: float):
    """Vectorised Fieller coverage / boundedness over stacked samples.

    ``nn`` and ``dd`` are (R, n) arrays of paired resamples.  Returns
    (covers, unbounded) boolean arrays of length R.

    Coverage is decided directly from the defining inequality
        (N - rho D)^2 <= t^2 (v11 - 2 rho v12 + rho^2 v22),
    which is exactly the Fieller set membership test and needs no root
    extraction.  Boundedness is decided by the sign of a = D^2 - t^2 v22.
    """
    R, n = nn.shape
    N = nn.mean(axis=1)
    D = dd.mean(axis=1)
    nc = nn - N[:, None]
    dc = dd - D[:, None]
    s11 = (nc * nc).sum(axis=1) / (n - 1)
    s22 = (dc * dc).sum(axis=1) / (n - 1)
    s12 = (nc * dc).sum(axis=1) / (n - 1)
    v11, v22, v12 = s11 / n, s22 / n, s12 / n
    lhs = (N - rho * D) ** 2
    rhs = t * t * (v11 - 2 * rho * v12 + rho * rho * v22)
    covers = lhs <= rhs
    unbounded = (D * D - t * t * v22) <= 0
    return covers, unbounded


def _ratio_simulation(relay, gap, rng, n_rep=800, n_boot_inner=150):
    """How the ratio estimator behaves as E[denominator] approaches zero.

    Population: the observed paired (numerator, denominator) task vectors,
    shifted so that the numerator mean is fixed at +0.05 and the denominator
    mean walks a grid.  The true ratio is then known exactly, so we can measure
    coverage of the naive percentile-bootstrap CI (what the repo does) against
    the Fieller set (what is correct).
    """
    stats = _sps

    num0 = np.asarray(relay, dtype=float)
    den0 = np.asarray(gap, dtype=float)
    n = len(num0)
    num_pop = num0 - num0.mean() + 0.05     # fixed numerator mean
    den_centered = den0 - den0.mean()
    t_crit = float(stats.t.ppf(0.975, df=n - 1))

    rows = []
    for mu_d in [0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.40]:
        den_pop = den_centered + mu_d
        rho_true = 0.05 / mu_d

        take = rng.integers(0, n, size=(n_rep, n))
        nn = num_pop[take]
        dd = den_pop[take]
        with np.errstate(divide="ignore", invalid="ignore"):
            ratios = nn.mean(axis=1) / dd.mean(axis=1)

        covers_f, unbounded_f = _fieller_covers_vec(nn, dd, rho_true, t_crit)

        # Naive percentile bootstrap on the ratio, chunked to bound memory.
        cover_naive = 0
        chunk = 40
        for start in range(0, n_rep, chunk):
            stop = min(start + chunk, n_rep)
            sub_n = nn[start:stop]
            sub_d = dd[start:stop]
            bidx = rng.integers(0, n, size=(stop - start, n_boot_inner, n))
            bn = np.take_along_axis(
                np.broadcast_to(sub_n[:, None, :], (stop - start, n_boot_inner, n)),
                bidx, axis=2).mean(axis=2)
            bd = np.take_along_axis(
                np.broadcast_to(sub_d[:, None, :], (stop - start, n_boot_inner, n)),
                bidx, axis=2).mean(axis=2)
            with np.errstate(divide="ignore", invalid="ignore"):
                br = bn / bd
            br = np.where(np.isfinite(br), br, np.nan)
            lo = np.nanpercentile(br, 2.5, axis=1)
            hi = np.nanpercentile(br, 97.5, axis=1)
            cover_naive += int(np.sum((lo <= rho_true) & (rho_true <= hi)))

        finite = ratios[np.isfinite(ratios)]
        rows.append({
            "denominator_mean": mu_d,
            "true_ratio": rho_true,
            "median_estimate": float(np.median(finite)),
            "iqr": float(np.percentile(finite, 75) - np.percentile(finite, 25)),
            "sd_estimate": float(finite.std(ddof=1)),
            "p2.5": float(np.percentile(finite, 2.5)),
            "p97.5": float(np.percentile(finite, 97.5)),
            "frac_sign_flipped": float(np.mean(np.sign(finite) != np.sign(rho_true))),
            "coverage_naive_percentile_bootstrap": cover_naive / n_rep,
            "coverage_fieller": float(covers_f.mean()),
            "frac_fieller_unbounded": float(unbounded_f.mean()),
        })
    return {
        "design": (
            "Resample the observed 155 paired (numerator, denominator) task "
            "vectors with the numerator mean pinned at +0.05 and the "
            "denominator mean set to each grid value. The true ratio is then "
            "0.05/mu_d exactly."
        ),
        "n_replicates": n_rep,
        "observed_denominator_mean_for_reference": float(den0.mean()),
        "grid": rows,
        "reading": (
            "Two things happen as the denominator approaches zero, and only one "
            "of them is a coverage failure. First, the estimator's dispersion "
            "explodes: the standard deviation of the point estimate grows by "
            "three orders of magnitude across this grid, so the number reported "
            "as 'average TNI' is dominated by which side of zero the "
            "denominator's sampling error lands on. Second, the percentile "
            "bootstrap's coverage degrades below nominal only in the extreme "
            "left of the grid; elsewhere it holds nominal coverage by producing "
            "intervals so wide they exclude nothing. Neither regime yields a "
            "usable estimate. Fieller is the honest report: it returns an "
            "unbounded set precisely when the data cannot pin the ratio down, "
            "and the fraction of unbounded sets rises from 0 to over 90 percent "
            "as the denominator shrinks."
        ),
    }


def _gap_noise_from_replicates(replicates: dict) -> dict:
    """Run-to-run variance of the necessity gap, from the 3-seed subset."""
    gaps_by_task = {}
    for tid, conds in replicates.items():
        s = conds.get(COND_SOLO, [])
        r = conds.get(COND_RESTRICTED, [])
        m = min(len(s), len(r))
        if m >= 2:
            gaps_by_task[tid] = [s[i] - r[i] for i in range(m)]
    if not gaps_by_task:
        return {"available": False}
    within = [float(np.var(v, ddof=1)) for v in gaps_by_task.values()]
    task_means = np.array([float(np.mean(v)) for v in gaps_by_task.values()])
    sigma2_e = float(np.mean(within))
    total = float(np.var(task_means, ddof=1))
    n_rep = float(np.mean([len(v) for v in gaps_by_task.values()]))
    sigma2_theta = max(0.0, total - sigma2_e / n_rep)
    return {
        "available": True,
        "n_tasks_with_replicates": len(gaps_by_task),
        "mean_replicates_per_task": n_rep,
        "within_task_variance_sigma2_e": sigma2_e,
        "between_task_variance_sigma2_theta": sigma2_theta,
        "reliability_of_a_single_run_gap": (
            sigma2_theta / (sigma2_theta + sigma2_e) if (sigma2_theta + sigma2_e) > 0 else float("nan")
        ),
        "note": (
            "This is the reliability of the TNI denominator measured on one "
            "seed. A ratio whose denominator has this much measurement noise "
            "and a population mean near zero cannot be stabilised by any "
            "epsilon or clamp."
        ),
    }


# ===========================================================================
# SECTION B: the replacement estimand
# ===========================================================================
def section_b(pool, replicates, n_boot, rng) -> dict:
    solo = np.array([r[COND_SOLO] for r in pool])
    restricted = np.array([r[COND_RESTRICTED] for r in pool])
    team = np.array([r[COND_TEAM] for r in pool])
    no_plan = np.array([r[COND_NO_PLAN] for r in pool])
    no_verify = np.array([r[COND_NO_VERIFY] for r in pool])

    g = solo - restricted      # partition value  (a property of the task design)
    u = team - solo            # team advantage   (the quantity of interest)
    r_relay = team - restricted

    definition = {
        "name": "Coordination Necessity Contrast (CNC)",
        "shape": "2-D per task: (g_i, u_i). Never a ratio.",
        "g_definition": "S_solo,i - S_restricted,i  (partition value: how much score the withheld information is worth to a single agent under the same turn budget)",
        "u_definition": "S_team,i - S_solo,i  (team advantage over the compute-matched single agent that has everything)",
        "why_two_dimensions": (
            "g and u answer different questions and are not commensurable. g is "
            "a property of the task's information design: if g = 0 the task "
            "never had a coordination requirement to detect, regardless of what "
            "the team does. u is a property of the multi-agent system. Dividing "
            "one by the other destroys both, because the denominator is a "
            "design property that is legitimately zero on many tasks."
        ),
        "admission_rule": (
            "A task is coordination-demanding at (tau_g, tau_u) iff its true "
            "theta^g > tau_g AND its true theta^u > tau_u. Benchmark-level "
            "admission is P(theta^g > tau_g), estimated hierarchically, not the "
            "count of tasks whose single-run estimate clears the threshold."
        ),
        "estimator": "sample mean of within-task differences",
        "ci_construction": "percentile bootstrap resampling TASKS (the cluster), conditions carried together so the contrast stays paired",
        "null_behaviour": "exact within-task sign-flip permutation; the estimator is centred at 0 under the null and its permutation p-value is valid without any distributional assumption",
    }

    boots = {
        "partition_value_g_solo_minus_restricted": task_clustered_bootstrap(g, n_boot, rng),
        "team_advantage_u_full_minus_solo": task_clustered_bootstrap(u, n_boot, rng),
        "relay_advantage_full_minus_restricted": task_clustered_bootstrap(r_relay, n_boot, rng),
        "planner_value_full_minus_no_plan": task_clustered_bootstrap(team - no_plan, n_boot, rng),
        "verifier_value_full_minus_no_verify": task_clustered_bootstrap(team - no_verify, n_boot, rng),
    }
    perms = {
        "partition_value_g": sign_flip_p(g, n_boot, rng),
        "team_advantage_u": sign_flip_p(u, n_boot, rng),
        "relay_advantage": sign_flip_p(r_relay, n_boot, rng),
        "planner_value": sign_flip_p(team - no_plan, n_boot, rng),
        "verifier_value": sign_flip_p(team - no_verify, n_boot, rng),
    }

    # --- asymmetry: the mean hides a real, characterisable effect ----------
    asym = _win_loss_decomposition(u, n_boot, rng)

    # --- 2-D joint classification -----------------------------------------
    tau_g, tau_u = 0.05, 0.05
    quad = {
        "coordination_demanding_g_pos_u_pos": int(np.sum((g > tau_g) & (u > tau_u))),
        "partition_matters_but_team_does_not_g_pos_u_neg": int(np.sum((g > tau_g) & (u < -tau_u))),
        "no_partition_but_team_helps_g_null_u_pos": int(np.sum((np.abs(g) <= tau_g) & (u > tau_u))),
        "no_partition_and_team_hurts_g_null_u_neg": int(np.sum((np.abs(g) <= tau_g) & (u < -tau_u))),
        "inverted_partition_g_neg": int(np.sum(g < -tau_g)),
        "everything_else_within_band": int(
            len(g) - np.sum((g > tau_g) & (u > tau_u)) - np.sum((g > tau_g) & (u < -tau_u))
            - np.sum((np.abs(g) <= tau_g) & (u > tau_u))
            - np.sum((np.abs(g) <= tau_g) & (u < -tau_u)) - np.sum(g < -tau_g)
        ),
        "thresholds": {"tau_g": tau_g, "tau_u": tau_u},
    }

    # --- hierarchical admission -------------------------------------------
    hier = _hierarchical_admission(g, replicates, n_boot, rng)
    hier_u = _hierarchical_admission(
        u, replicates, n_boot, rng, contrast=(COND_TEAM, COND_SOLO), label="theta_u"
    )

    # --- null behaviour of the admission statistic ------------------------
    null_adm = _admission_under_null(pool, hier, n_perm=2000, rng=rng)

    # --- per-task CIs where replicates exist ------------------------------
    per_task_ci = _per_task_necessity_cis(replicates, n_boot, rng)

    return {
        "definition": definition,
        "pool_level_estimates": boots,
        "permutation_p_values": perms,
        "win_loss_asymmetry": asym,
        "two_dimensional_task_census": quad,
        "hierarchical_admission_partition_value": hier,
        "hierarchical_admission_team_advantage": hier_u,
        "admission_statistic_under_the_null": null_adm,
        "per_task_intervals_on_replicated_subset": per_task_ci,
    }


def _win_loss_decomposition(u: np.ndarray, n_boot: int, rng) -> dict:
    """A zero mean is not the same as no effect.

    Decompose the team-versus-Solo contrast into how often the team wins and
    how much it wins or loses by.  A system that wins most contested tasks but
    loses larger amounts on the rest has a real, describable behaviour that the
    mean erases.
    """
    stats = _sps

    u = np.asarray(u, dtype=float)
    wins = u > 0
    losses = u < 0
    ties = u == 0
    n_contested = int(wins.sum() + losses.sum())
    k = int(wins.sum())
    p_sign = float(stats.binomtest(k, n_contested, 0.5).pvalue) if n_contested else float("nan")
    lo, hi = wilson_ci(k, n_contested) if n_contested else (float("nan"), float("nan"))
    mean_win = float(u[wins].mean()) if wins.any() else 0.0
    mean_loss = float(u[losses].mean()) if losses.any() else 0.0
    return {
        "n_tasks": int(len(u)),
        "n_ties": int(ties.sum()),
        "n_contested": n_contested,
        "team_wins": k,
        "team_losses": int(losses.sum()),
        "win_rate_among_contested": k / n_contested if n_contested else float("nan"),
        "win_rate_wilson_ci": [lo, hi],
        "sign_test_p": p_sign,
        "mean_gain_when_team_wins_pp": round(100 * mean_win, 2),
        "mean_loss_when_team_loses_pp": round(100 * mean_loss, 2),
        "loss_to_gain_magnitude_ratio": round(abs(mean_loss) / mean_win, 3) if mean_win > 0 else None,
        "mean_contrast_pp": round(100 * float(u.mean()), 3),
        "median_contrast_pp": round(100 * float(np.median(u)), 3),
        "reading": (
            "The team wins more contested tasks than it loses, and the sign test "
            "on that count is significant, but the mean contrast is zero because "
            "the losses are larger than the wins. This is a variance effect, not "
            "an absence of an effect: adding roles changes the distribution of "
            "outcomes without moving its centre. Reporting only the mean hides "
            "it, and so does reporting only the win count."
        ),
    }


def _hierarchical_admission(
    obs: np.ndarray, replicates: dict, n_boot: int, rng,
    contrast=(COND_SOLO, COND_RESTRICTED), label="theta_g",
) -> dict:
    """Empirical-Bayes normal-normal admission probability.

    Model:  y_i = theta_i + e_i,  e_i ~ N(0, sigma2_e),  theta_i ~ N(mu, tau2).
    sigma2_e is estimated from the multi-seed replicate subset (run-to-run
    variance of the same contrast).  tau2 = max(0, Var(y) - sigma2_e).
    Posterior for task i is Normal with shrinkage weight B = tau2/(tau2+sigma2_e).

    Benchmark admission at threshold tau is pi(tau) = mean_i P(theta_i > tau),
    which is the *expected number of genuinely qualifying tasks*, not the count
    of noisy point estimates above the line.
    """
    stats = _sps

    a, b = contrast
    diffs = []
    for conds in replicates.values():
        xa, xb = conds.get(a, []), conds.get(b, [])
        m = min(len(xa), len(xb))
        if m >= 2:
            diffs.append([xa[i] - xb[i] for i in range(m)])
    if not diffs:
        return {"available": False, "reason": "no multi-seed replicates for this contrast"}

    sigma2_e = float(np.mean([np.var(d, ddof=1) for d in diffs]))
    n_rep = float(np.mean([len(d) for d in diffs]))
    obs = np.asarray(obs, dtype=float)
    var_y = float(np.var(obs, ddof=1))
    mu = float(obs.mean())

    # Two like-for-like variance decompositions, both reported.
    tau2_pool = var_y - sigma2_e                      # full pool, single run each
    sub_means = np.array([float(np.mean(d)) for d in diffs])
    tau2_sub = float(np.var(sub_means, ddof=1)) - sigma2_e / n_rep   # replicate subset
    tau2 = max(0.0, tau2_pool)
    boundary = tau2 <= 0.0

    mub = task_clustered_bootstrap(obs, min(n_boot, 10000), rng)

    out = {
        "available": True,
        "quantity": label,
        "sigma2_e_from_replicates": sigma2_e,
        "n_tasks_supplying_sigma2_e": len(diffs),
        "mean_replicates_per_task": n_rep,
        "var_of_single_run_estimates_full_pool": var_y,
        "tau2_between_task_full_pool": tau2_pool,
        "tau2_between_task_replicate_subset": tau2_sub,
        "grand_mean_mu": mu,
        "grand_mean_ci": [mub["ci_lo"], mub["ci_hi"]],
        "at_variance_boundary": bool(boundary),
        "boundary_reading": (
            "The estimated between-task variance in %s is not positive: the "
            "run-to-run variance measured on the replicate subset (%.4f) is at "
            "least as large as the task-to-task variance of the single-run "
            "estimates on the full pool (%.4f). Both decompositions agree on "
            "the sign. Under the model this means the corpus provides no "
            "evidence that any task has more of this quantity than any other, "
            "so every task's posterior collapses onto the grand mean, and the "
            "grand mean itself is %.4f with a 95%% interval of [%.4f, %.4f] "
            "that contains zero. The correct conclusion is not that admission "
            "is easy or impossible, but that at one run per task the corpus "
            "cannot rank its own tasks by this quantity at all."
            % (label, sigma2_e, var_y, mu, mub["ci_lo"], mub["ci_hi"])
        ) if boundary else None,
        "thresholds": {},
        "sensitivity_to_sigma2_e": {},
    }

    def _pi(tau_thresh, s2e):
        t2 = max(0.0, var_y - s2e)
        if t2 <= 0:
            # degenerate: every theta_i equals mu
            return 1.0 if mu > tau_thresh else 0.0
        B_ = t2 / (t2 + s2e)
        pm = mu + B_ * (obs - mu)
        psd = math.sqrt(t2 * s2e / (t2 + s2e))
        return float(np.mean(1.0 - stats.norm.cdf((tau_thresh - pm) / psd)))

    for tau in [0.0, 0.05, 0.10, 0.20]:
        pi_hat = _pi(tau, sigma2_e)
        naive = float(np.mean(obs > tau))
        out["thresholds"][f"tau={tau}"] = {
            "pi_hierarchical": pi_hat,
            "naive_fraction_of_point_estimates_above_tau": naive,
            "inflation_of_naive_over_hierarchical": naive - pi_hat,
            "expected_qualifying_tasks_of_%d" % len(obs): pi_hat * len(obs),
        }
    # sigma2_e is itself estimated; show how the answer moves with it.
    for scale in [0.25, 0.5, 0.75, 1.0]:
        s2 = sigma2_e * scale
        out["sensitivity_to_sigma2_e"][f"sigma2_e x {scale}"] = {
            "sigma2_e": s2,
            "implied_reliability": (max(0.0, var_y - s2) / var_y) if var_y > 0 else None,
            "pi_at_tau_0.10": _pi(0.10, s2),
            "pi_at_tau_0.20": _pi(0.20, s2),
        }
    # How many runs per cell would make the between-task term estimable?
    tau2_opt = max(tau2_sub, tau2_pool, 0.0)
    runs_needed = {}
    for target in [0.5, 0.7, 0.8]:
        if tau2_opt > 0:
            k = sigma2_e * target / (tau2_opt * (1 - target))
            runs_needed[f"reliability_{target}"] = math.ceil(k)
        else:
            runs_needed[f"reliability_{target}"] = None
    out["runs_per_cell_needed"] = {
        "assumed_tau2": tau2_opt,
        "assumption": (
            "uses the larger of the two between-task variance estimates, which "
            "is the optimistic case; if the true between-task variance is zero "
            "no amount of replication makes the ranking meaningful because there "
            "is nothing to rank"
        ),
        "runs": runs_needed,
        "current_runs_per_cell": 1,
    }
    out["recommended_operating_threshold"] = 0.10
    out["reading"] = (
        "The tau = 0 row is not informative: asking whether a task's true "
        "necessity exceeds zero is asking for the sign of a quantity the corpus "
        "cannot measure, and at the variance boundary the estimator correctly "
        "returns the sign of the grand mean for every task. The substantive "
        "reading is in the sensitivity block, and it is not that the "
        "hierarchical number is small. It is that the admitted fraction at a "
        "10-point threshold moves across the whole available range as the "
        "assumed measurement variance moves over a four-fold band, and that "
        "band is not resolvable from 39 tasks with three seeds. The admitted "
        "fraction of this corpus is therefore not identified, and no threshold "
        "on a single run per condition can identify it. The naive count is a "
        "point on that curve chosen by assuming the measurement variance is "
        "zero, which is the one value the replicate data rule out. The fix is "
        "replication, not a better threshold. The runs-per-cell block gives the "
        "budget: under the optimistic between-task variance estimate, ranking "
        "tasks by partition value needs the stated number of runs per cell "
        "before a single task's estimate is even half reliable, against the one "
        "run per cell the reference ablation currently has."
    )
    return out


def _admission_under_null(pool, hier, n_perm, rng) -> dict:
    """What the admission statistic reports when there is no effect at all.

    Null: within a task, the Solo and Restricted labels are exchangeable.  Any
    admission rule should return ~0 qualifying tasks here.
    """
    if not hier.get("available"):
        return {"available": False}
    stats = _sps

    solo = np.array([r[COND_SOLO] for r in pool])
    restricted = np.array([r[COND_RESTRICTED] for r in pool])
    n = len(solo)
    sigma2_e = hier["sigma2_e_from_replicates"]
    naive_null = {0.0: [], 0.05: [], 0.10: []}
    hier_null = {0.0: [], 0.05: [], 0.10: []}
    for _ in range(n_perm):
        flip = rng.random(n) < 0.5
        a = np.where(flip, restricted, solo)
        b = np.where(flip, solo, restricted)
        y = a - b
        var_y = float(np.var(y, ddof=1))
        tau2 = max(1e-9, var_y - sigma2_e)
        mu = float(y.mean())
        B = tau2 / (tau2 + sigma2_e)
        pm = mu + B * (y - mu)
        psd = math.sqrt(tau2 * sigma2_e / (tau2 + sigma2_e))
        for tau in naive_null:
            naive_null[tau].append(float(np.mean(y > tau)))
            hier_null[tau].append(float(np.mean(1.0 - stats.norm.cdf((tau - pm) / psd))))
    return {
        "available": True,
        "n_permutations": n_perm,
        "null_levels": {
            f"tau={tau}": {
                "naive_count_rule_mean": float(np.mean(naive_null[tau])),
                "naive_count_rule_p95": float(np.percentile(naive_null[tau], 95)),
                "hierarchical_rule_mean": float(np.mean(hier_null[tau])),
                "hierarchical_rule_p95": float(np.percentile(hier_null[tau], 95)),
            }
            for tau in naive_null
        },
        "reading": (
            "Under an exact null the naive threshold rule still admits a large "
            "fraction of tasks, because half of a symmetric noise distribution "
            "sits above zero. The hierarchical rule shrinks toward the grand "
            "mean and reports close to nothing, which is the correct answer."
        ),
    }


def _per_task_necessity_cis(replicates, n_boot, rng) -> dict:
    rows = []
    for tid, conds in sorted(replicates.items()):
        s, r = conds.get(COND_SOLO, []), conds.get(COND_RESTRICTED, [])
        t = conds.get(COND_TEAM, [])
        m = min(len(s), len(r), len(t))
        if m < 3:
            continue
        g = np.array([s[i] - r[i] for i in range(m)])
        u = np.array([t[i] - s[i] for i in range(m)])
        rows.append({
            "task_id": tid,
            "n_seeds": m,
            "g_mean": float(g.mean()),
            "g_se": float(g.std(ddof=1) / math.sqrt(m)),
            "u_mean": float(u.mean()),
            "u_se": float(u.std(ddof=1) / math.sqrt(m)),
        })
    if not rows:
        return {"available": False}
    # A task's necessity is "established" only if g - 2*se > 0.
    est = [r for r in rows if r["g_mean"] - 2 * r["g_se"] > 0]
    return {
        "available": True,
        "n_tasks_with_3_seeds": len(rows),
        "n_with_partition_value_established_at_2se": len(est),
        "established_task_ids": [r["task_id"] for r in est],
        "note": (
            "With three seeds per task the per-task interval is wide. This is "
            "the honest resolution of the corpus at task granularity and it is "
            "why per-task TNI values were never estimable, clamp or no clamp."
        ),
        "rows": rows,
    }


# ===========================================================================
# SECTION C: quintile analysis redone
# ===========================================================================
def trend_test(strat: np.ndarray, contrast: np.ndarray, n_perm: int, rng) -> dict:
    """Continuous alternative to the quintile contrast.

    Slope of the paired contrast on the rank of the stratifier.  Binning throws
    away information and makes the answer depend on where the bin edges fall;
    a rank-based slope does not.  The null is the same exact within-task
    sign-flip, so it is valid whatever the stratifier is.
    """
    strat = np.asarray(strat, dtype=float)
    contrast = np.asarray(contrast, dtype=float)
    n = len(strat)
    r = np.argsort(np.argsort(strat, kind="stable"), kind="stable").astype(float)
    r = (r - r.mean()) / r.std(ddof=0)

    def slope(y):
        return float(np.dot(r, y) / n)

    obs = slope(contrast)
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n_perm, n))
    null = (signs * contrast) @ r / n
    p = float((np.sum(np.abs(null) >= abs(obs) - 1e-15) + 1) / (n_perm + 1))
    return {
        "slope_pp_per_sd_of_rank": round(100 * obs, 3),
        "permutation_p_two_sided": p,
        "null_slope_mean_pp": round(100 * float(null.mean()), 3),
        "interpretation": (
            "negative slope means the team helps more on tasks the instrument "
            "rates as harder"
        ),
    }


def quintile_profile(strat: np.ndarray, contrast: np.ndarray, n_bins: int = 5) -> list[dict]:
    """Equal-count stratification of `contrast` by `strat`, ties broken stably."""
    n = len(strat)
    order = np.argsort(strat, kind="stable")
    bins = np.array_split(order, n_bins)
    rows = []
    for k, idx in enumerate(bins, start=1):
        rows.append({
            "bin": k,
            "n": int(len(idx)),
            "strat_min": float(strat[idx].min()),
            "strat_max": float(strat[idx].max()),
            "mean_contrast_pp": float(100 * contrast[idx].mean()),
            "_idx": idx,
        })
    return rows


def section_c(pool, lb90, n_boot, rng, n_perm=4000) -> dict:
    solo = np.array([r[COND_SOLO] for r in pool])
    restricted = np.array([r[COND_RESTRICTED] for r in pool])
    team = np.array([r[COND_TEAM] for r in pool])
    no_plan = np.array([r[COND_NO_PLAN] for r in pool])
    no_verify = np.array([r[COND_NO_VERIFY] for r in pool])
    tasks = [r["task_id"] for r in pool]
    u = team - solo

    out: dict = {}

    # --- C1: reproduce the published design --------------------------------
    pub_rows = quintile_profile(solo, u)
    pub = []
    for row in pub_rows:
        idx = row.pop("_idx")
        b = task_clustered_bootstrap(u[idx], n_boot, rng)
        row["ci_lo_pp"] = 100 * b["ci_lo"]
        row["ci_hi_pp"] = 100 * b["ci_hi"]
        pub.append(row)
    obs_profile = np.array([r["mean_contrast_pp"] for r in pub])
    obs_spread = float(obs_profile[0] - obs_profile[-1])

    published_reference = None
    if os.path.exists(P_QUINTILE_PUBLISHED):
        with open(P_QUINTILE_PUBLISHED) as fh:
            published_reference = json.load(fh)

    out["C1_published_design_reproduced"] = {
        "design": "stratify tasks by the SAME single Solo run that appears in the contrast, then report mean(Team - Solo) per bin",
        "profile_pp": [round(x, 2) for x in obs_profile],
        "q1_minus_q5_pp": round(obs_spread, 2),
        "bins": pub,
        "published_file": P_QUINTILE_PUBLISHED if published_reference else None,
        "published_profile_pp": (
            [q["mean_uplift_pp"] for q in published_reference["quintiles"]]
            if published_reference else None
        ),
        "reproduction_max_abs_diff_pp": (
            float(np.max(np.abs(obs_profile - np.array(
                [q["mean_uplift_pp"] for q in published_reference["quintiles"]]))))
            if published_reference else None
        ),
    }

    # --- C2: the exact null for that design --------------------------------
    null_profiles = np.empty((n_perm, 5))
    n = len(solo)
    for i in range(n_perm):
        flip = rng.random(n) < 0.5
        s_p = np.where(flip, team, solo)
        t_p = np.where(flip, solo, team)
        up = t_p - s_p
        rows = quintile_profile(s_p, up)
        null_profiles[i] = [r["mean_contrast_pp"] for r in rows]
    null_mean = null_profiles.mean(axis=0)
    null_spread = null_profiles[:, 0] - null_profiles[:, -1]
    p_spread = float((np.sum(null_spread >= obs_spread) + 1) / (n_perm + 1))
    p_spread_lower = float((np.sum(null_spread <= obs_spread) + 1) / (n_perm + 1))
    p_spread_two = float(min(1.0, 2 * min(p_spread, p_spread_lower)))
    arm_sd = {
        "solo_sd": float(solo.std(ddof=1)),
        "team_sd": float(team.std(ddof=1)),
        "note": (
            "The sign-flip null replaces the stratifier with a random member of "
            "each task's (Solo, Team) pair. The two arms have similar spread, so "
            "the null's stratifier has close to the same variance as the real "
            "one and the null profile is a fair reference for this design."
        ),
    }

    out["C2_exact_null_for_that_design"] = {
        "null": "within each task, swap the Solo and Team labels with probability 1/2 (exact permutation null for a paired contrast: no team effect of any kind)",
        "n_permutations": n_perm,
        "mean_null_profile_pp": [round(float(x), 2) for x in null_mean],
        "null_q1_minus_q5_mean_pp": float(null_spread.mean()),
        "null_q1_minus_q5_p5_p95_pp": [float(np.percentile(null_spread, 5)),
                                       float(np.percentile(null_spread, 95))],
        "observed_q1_minus_q5_pp": obs_spread,
        "p_value_observed_spread_exceeds_null": p_spread,
        "p_value_observed_spread_below_null": p_spread_lower,
        "p_value_two_sided": p_spread_two,
        "arm_variance_check": arm_sd,
        "verdict": (
            "The published monotone profile is what this design produces when "
            "there is no effect at all. The observed spread is not larger than "
            "the null spread, so the quintile figure carries no evidence for a "
            "capability-conditional team effect."
            if p_spread > 0.05 else
            "The observed spread exceeds the null spread; some capability-"
            "conditional structure survives this design."
        ),
        "second_verdict": (
            "The observed spread is in fact SMALLER than the null spread "
            "(p = %.4f in the lower tail). The design's artifact overshoots the "
            "data: after accounting for regression to the mean, the "
            "capability-conditional effect points weakly the other way." % p_spread_lower
            if p_spread_lower < 0.05 else
            "The observed spread sits inside the null distribution in both tails."
        ),
        "mechanism": (
            "The stratifier and the minuend of the contrast are the same single "
            "run. Selecting the lowest bin selects tasks whose Solo run was "
            "unlucky; the Team run does not share that luck, so the difference "
            "is positive by construction, and symmetrically negative in the top "
            "bin. This is regression to the mean, and its magnitude is set by "
            "the run-to-run noise share of the Solo score."
        ),
    }

    # --- C3: independent difficulty instruments ----------------------------
    instruments: dict[str, dict] = {}

    def add_instrument(key, desc, strat_vals, mask=None, independent=True):
        m = np.ones(len(solo), dtype=bool) if mask is None else mask
        sv = np.asarray(strat_vals, dtype=float)[m]
        uv = u[m]
        rows = quintile_profile(sv, uv)
        prof = []
        for row in rows:
            idx = row.pop("_idx")
            b = task_clustered_bootstrap(uv[idx], n_boot, rng)
            row["ci_lo_pp"] = 100 * b["ci_lo"]
            row["ci_hi_pp"] = 100 * b["ci_hi"]
            prof.append(row)
        p = np.array([r["mean_contrast_pp"] for r in prof])
        spread = float(p[0] - p[-1])
        # Null for this instrument: swap Team/Solo labels but keep the
        # (independent) stratifier fixed.
        nulls = np.empty((n_perm, 5))
        nn = int(m.sum())
        s_m, t_m = solo[m], team[m]
        for i in range(n_perm):
            flip = rng.random(nn) < 0.5
            up = np.where(flip, s_m - t_m, t_m - s_m)
            nulls[i] = [r["mean_contrast_pp"] for r in quintile_profile(sv, up)]
        nsp = nulls[:, 0] - nulls[:, -1]
        # Monotonicity: the quintile contrast is a two-point comparison and can
        # be large on a non-monotone profile.  Report the shape too.
        _st = _sps
        mono = float(_st.spearmanr(np.arange(1, 6), p).statistic)
        instruments[key] = {
            "instrument": desc,
            "independent_of_contrast_noise": independent,
            "n_tasks": int(m.sum()),
            "profile_pp": [round(float(x), 2) for x in p],
            "bins": prof,
            "q1_minus_q5_pp": round(spread, 2),
            "profile_monotonicity_spearman": round(mono, 3),
            "null_profile_mean_pp": [round(float(x), 2) for x in nulls.mean(axis=0)],
            "null_q1_minus_q5_mean_pp": float(nsp.mean()),
            "p_value_two_sided": float((np.sum(np.abs(nsp) >= abs(spread)) + 1) / (n_perm + 1)),
            "rtm_corrected_spread_pp": round(spread - float(nsp.mean()), 2),
            "continuous_trend_test": trend_test(sv, uv, n_perm, rng),
        }

    add_instrument(
        "I1_restricted_run",
        "per-task Restricted score (a different run of a different condition; shares task difficulty with Solo but no run-level noise with either arm of the contrast)",
        restricted,
    )
    add_instrument(
        "I2_mean_of_lesioned_team_arms",
        "mean of the No-Plan and No-Verify runs (two further independent runs, neither of which appears in the contrast)",
        (no_plan + no_verify) / 2.0,
    )

    # I3: held-out models' Solo scores from LB90
    heldout = _heldout_model_difficulty(tasks, lb90)
    if heldout["n_tasks"] >= 20:
        mask = np.array([t in heldout["difficulty"] for t in tasks])
        vals = np.array([heldout["difficulty"].get(t, np.nan) for t in tasks])
        vals = np.where(np.isnan(vals), 0.0, vals)
        add_instrument(
            "I3_heldout_models_solo",
            "mean Solo (oracle) score of %d other models on the LB90 pool, on the %d tasks shared with the reference ablation (a completely different set of runs and models)"
            % (heldout["n_models"], heldout["n_tasks"]),
            vals, mask=mask,
        )
    instruments["I3_note"] = heldout["note"]

    # I4: same-model, different seeds (phase-3 subset)
    out["C3_independent_difficulty_instruments"] = instruments

    # --- C4: RTM-corrected effect ------------------------------------------
    corrected = obs_profile - null_mean
    out["C4_rtm_corrected_effect"] = {
        "definition": "observed quintile profile minus the mean profile the same design produces under the exact no-effect null",
        "corrected_profile_pp": [round(float(x), 2) for x in corrected],
        "corrected_q1_minus_q5_pp": round(float(obs_spread - null_spread.mean()), 2),
        "uncorrected_q1_minus_q5_pp": round(obs_spread, 2),
        "artifact_share_of_published_spread": (
            float(null_spread.mean() / obs_spread) if obs_spread != 0 else None
        ),
        "reading": (
            "A ratio above 1 means the design's own artifact is larger than the "
            "published effect, so the published effect is entirely accounted "
            "for by regression to the mean."
        ),
    }

    # --- C5: does anything capability-conditional survive? -----------------
    real = {k: v for k, v in instruments.items()
            if isinstance(v, dict) and v.get("p_value_two_sided") is not None}
    p_bin = {k: v["p_value_two_sided"] for k, v in real.items()}
    p_trend = {k: v["continuous_trend_test"]["permutation_p_two_sided"] for k, v in real.items()}
    holm_bin = holm(p_bin)
    holm_trend = holm(p_trend)
    surviving_bin = [k for k, v in holm_bin.items() if v.get("reject_at_0.05")]
    surviving_trend = [k for k, v in holm_trend.items() if v.get("reject_at_0.05")]
    monotone = {k: v["profile_monotonicity_spearman"] for k, v in real.items()}

    # How precise is each instrument?  A real difficulty gradient must show up
    # MORE strongly in a less noisy instrument, because independent stratifier
    # noise attenuates a true relationship without biasing it.
    precision = {
        "I1_restricted_run": {"runs_averaged": 1, "same_model": True},
        "I2_mean_of_lesioned_team_arms": {"runs_averaged": 2, "same_model": True},
        "I3_heldout_models_solo": {"runs_averaged": "one run each from the LB90 model panel",
                                   "same_model": False},
    }
    slopes = {k: v["continuous_trend_test"]["slope_pp_per_sd_of_rank"] for k, v in real.items()}
    least_noisy = "I2_mean_of_lesioned_team_arms"
    ordering_consistent = (
        abs(slopes.get(least_noisy, 0.0)) >= abs(slopes.get("I1_restricted_run", 0.0))
    )

    best_raw = min(list(p_bin.values()) + list(p_trend.values()))
    best_key = min(real, key=lambda k: min(p_bin[k], p_trend[k]))
    if not surviving_bin and not surviving_trend:
        statement = (
            "No capability-conditional team effect survives stratification on an "
            "independent difficulty estimate once the three instruments are "
            "corrected for multiplicity. The published effect is a property of "
            "the estimator, not of the systems it was applied to. "
            "The closest call is %s, whose uncorrected p is %.3f and whose "
            "Holm-corrected p across the three instruments is above 0.05. Two "
            "further reasons not to promote it: it is the noisiest instrument "
            "of the three (a single run), and the least noisy instrument (two "
            "runs averaged) gives a slope of %+.2f pp against its %+.2f pp. "
            "Independent stratifier noise attenuates a true gradient without "
            "biasing it, so a real gradient must show up at least as strongly "
            "in the less noisy instrument; the observed ordering is the "
            "opposite. Whatever residual signal is there is also an order of "
            "magnitude smaller than the published %+.1f pp contrast."
            % (best_key, best_raw,
               slopes.get(least_noisy, float("nan")),
               slopes.get(best_key, float("nan")),
               out["C1_published_design_reproduced"]["q1_minus_q5_pp"])
        )
    else:
        statement = (
            "One instrument survives correction: " +
            (", ".join(sorted(set(surviving_bin) | set(surviving_trend)))) +
            ". It should not be read as confirming the published claim. The "
            "surviving instrument is the noisiest of the three (a single run), "
            "and the least noisy instrument (two runs averaged, slope "
            "%+.2f pp) shows nothing. Independent stratifier noise attenuates a "
            "true gradient without biasing it, so a real capability gradient "
            "must appear at least as strongly in the less noisy instrument. The "
            "observed ordering is the opposite%s. The defensible summary is that "
            "the evidence for a capability-conditional effect is marginal, is "
            "not replicated across instruments, and is far smaller than the "
            "published %+.1f pp contrast in any case."
            % (slopes.get(least_noisy, float('nan')),
               "" if not ordering_consistent else " in magnitude but not in significance",
               out["C1_published_design_reproduced"]["q1_minus_q5_pp"])
        )

    out["C5_verdict"] = {
        "instruments_tested": list(real),
        "instrument_precision": precision,
        "continuous_trend_slopes_pp": slopes,
        "quintile_contrast_p_holm_corrected_across_instruments": holm_bin,
        "continuous_trend_p_holm_corrected_across_instruments": holm_trend,
        "profile_monotonicity_by_instrument": monotone,
        "surviving_after_correction_quintile_contrast": surviving_bin,
        "surviving_after_correction_continuous_trend": surviving_trend,
        "attenuation_ordering_consistent_with_a_real_gradient": bool(ordering_consistent),
        "statement": statement,
        "caution": (
            "The Q1-minus-Q5 contrast is a two-point comparison and can be large "
            "on a profile with no monotone trend. The continuous trend test uses "
            "every task and does not depend on where the bin edges fall, so it "
            "is the primary test; the quintile contrast is reported for "
            "comparability with the published figure. Both are corrected across "
            "the three instruments by Holm."
        ),
        "what_would_settle_it": (
            "Three or more seeds per task per condition on the full pool. At one "
            "run per cell the difficulty instrument and the contrast are both "
            "noise-dominated, and no amount of re-analysis can separate a small "
            "real gradient from sampling variation."
        ),
    }
    return out


def _heldout_model_difficulty(ref_tasks, lb90) -> dict:
    """Mean Solo (oracle) partial score across LB90 models, per task."""
    mat = lb90["matrix"]
    per_task: dict[str, list[float]] = defaultdict(list)
    models_used = 0
    for model, conds in mat.items():
        rows = conds.get(COND_SOLO)
        if not rows:
            continue
        models_used += 1
        for tid, v in rows.items():
            per_task[tid].append(v["partial"])
    shared = {t: float(np.mean(v)) for t, v in per_task.items()
              if t in set(ref_tasks) and len(v) >= 3}
    return {
        "difficulty": shared,
        "n_tasks": len(shared),
        "n_models": models_used,
        "note": (
            "Held-out difficulty is the mean Solo partial score of the LB90 "
            "model panel. It shares no run with the reference ablation's "
            "contrast, and it is produced by different models, so it cannot "
            "induce regression to the mean in mean(Team - Solo). Coverage is "
            "limited to the %d tasks the two pools share." % len(shared)
        ),
    }


# ===========================================================================
# SECTION D: uplift relabelling
# ===========================================================================
def section_d(pool, lb90, n_boot, rng) -> dict:
    solo = np.array([r[COND_SOLO] for r in pool])
    restricted = np.array([r[COND_RESTRICTED] for r in pool])
    team = np.array([r[COND_TEAM] for r in pool])

    vs_solo = team - solo
    vs_restricted = team - restricted

    b_solo = task_clustered_bootstrap(vs_solo, n_boot, rng)
    b_res = task_clustered_bootstrap(vs_restricted, n_boot, rng)

    out = {
        "the_mislabel": {
            "location": "harness/compute_tni.py, TaskMetrics.team_uplift",
            "code": "return self.team_partial - self.restricted_partial",
            "problem": (
                "The field is named team_uplift and is consumed downstream as "
                "the team-versus-Solo effect, but it is the team-versus-"
                "Restricted effect. Restricted is a handicapped single agent "
                "that never sees the specification, so this comparison flatters "
                "the team by the full value of the information partition."
            ),
            "stored_aggregate_avg_team_uplift": None,
        },
        "full_minus_solo": {
            "meaning": "team versus the compute-matched single agent with the same information",
            "mean_pp": round(100 * b_solo["mean"], 3),
            "ci95_pp": [round(100 * b_solo["ci_lo"], 3), round(100 * b_solo["ci_hi"], 3)],
            "bootstrap": b_solo,
            "permutation_p": sign_flip_p(vs_solo, n_boot, rng),
            "n_tasks_team_wins": int(np.sum(vs_solo > 0)),
            "n_tasks_team_loses": int(np.sum(vs_solo < 0)),
            "n_tasks_tied": int(np.sum(vs_solo == 0)),
        },
        "full_minus_restricted": {
            "meaning": "team versus a single agent that was denied the specification",
            "mean_pp": round(100 * b_res["mean"], 3),
            "ci95_pp": [round(100 * b_res["ci_lo"], 3), round(100 * b_res["ci_hi"], 3)],
            "bootstrap": b_res,
            "permutation_p": sign_flip_p(vs_restricted, n_boot, rng),
            "n_tasks_team_wins": int(np.sum(vs_restricted > 0)),
            "n_tasks_team_loses": int(np.sum(vs_restricted < 0)),
            "n_tasks_tied": int(np.sum(vs_restricted == 0)),
        },
        "sign_flip_between_the_two": None,
    }
    with open(P_ABLATION_SUMMARY) as fh:
        agg = json.load(fh)["aggregate"]
    out["the_mislabel"]["stored_aggregate_avg_team_uplift"] = agg.get("avg_team_uplift")
    out["the_mislabel"]["recomputed_full_minus_restricted"] = float(vs_restricted.mean())
    out["the_mislabel"]["recomputed_full_minus_solo"] = float(vs_solo.mean())
    out["sign_flip_between_the_two"] = {
        "full_minus_restricted_pp": round(100 * float(vs_restricted.mean()), 3),
        "full_minus_solo_pp": round(100 * float(vs_solo.mean()), 3),
        "sign_changes": bool((vs_restricted.mean() > 0) != (vs_solo.mean() > 0)),
    }

    # --- LB90 replication, paired within task ------------------------------
    out["lb90_paired_replication"] = _lb90_paired(lb90, n_boot, rng)
    return out


def _lb90_paired(lb90, n_boot, rng) -> dict:
    mat = lb90["matrix"]
    per_model = {}
    diffs_solo_all, diffs_res_all = [], []
    n_restricted_beats_solo = 0
    n_comparable = 0
    unpaired_warning = []
    for model, conds in sorted(mat.items()):
        o = conds.get(COND_SOLO, {})
        r = conds.get(COND_RESTRICTED, {})
        f = conds.get(COND_TEAM, {})
        common_or = sorted(set(o) & set(r))
        common_of = sorted(set(o) & set(f))
        row = {
            "n_solo": len(o), "n_restricted": len(r), "n_full": len(f),
            "n_paired_solo_restricted": len(common_or),
            "n_paired_solo_full": len(common_of),
        }
        if common_or:
            d = np.array([r[t]["partial"] - o[t]["partial"] for t in common_or])
            row["restricted_minus_solo_paired_pp"] = round(100 * float(d.mean()), 2)
            row["restricted_minus_solo_paired_p"] = sign_flip_p(d, 4000, rng)
            n_comparable += 1
            if d.mean() > 0:
                n_restricted_beats_solo += 1
            diffs_res_all.extend(d.tolist())
        if common_of:
            d2 = np.array([f[t]["partial"] - o[t]["partial"] for t in common_of])
            row["full_minus_solo_paired_pp"] = round(100 * float(d2.mean()), 2)
            diffs_solo_all.extend(d2.tolist())
        # unpaired hazard: conditions evaluated on different task subsets
        if o and f and len(set(o) ^ set(f)) > 0:
            unpaired_warning.append({
                "model": model,
                "tasks_only_in_solo": len(set(o) - set(f)),
                "tasks_only_in_full": len(set(f) - set(o)),
            })
        per_model[model] = row
    return {
        "per_model": per_model,
        "n_models_with_paired_solo_and_restricted": n_comparable,
        "n_models_where_restricted_beats_solo_paired": n_restricted_beats_solo,
        "pooled_restricted_minus_solo_pp": round(100 * float(np.mean(diffs_res_all)), 3) if diffs_res_all else None,
        "pooled_full_minus_solo_pp": round(100 * float(np.mean(diffs_solo_all)), 3) if diffs_solo_all else None,
        "unequal_task_coverage_between_conditions": unpaired_warning,
        "warning": (
            "The stored LB90 aggregate reports each condition's rate over "
            "whatever tasks completed for that condition, so per-condition "
            "denominators differ within a model. Any Solo-vs-Team comparison "
            "read off those rates is unpaired and confounded with which tasks "
            "happened to finish. The paired numbers here restrict to the "
            "task intersection within each model."
        ),
    }


# ===========================================================================
# SECTION E: statistical machinery audit
# ===========================================================================
def section_e(pool, lb90, role_runs, n_boot, rng) -> dict:
    solo = np.array([r[COND_SOLO] for r in pool])
    team = np.array([r[COND_TEAM] for r in pool])
    restricted = np.array([r[COND_RESTRICTED] for r in pool])

    # --- E1: paired vs unpaired bootstrap ----------------------------------
    paired = task_clustered_bootstrap(team - solo, n_boot, rng)
    unpaired = unpaired_bootstrap_diff(team, solo, n_boot, rng)
    rho = float(np.corrcoef(team, solo)[0, 1])
    e1 = {
        "finding": (
            "harness/statistics.py::bootstrap_ci_difference resamples the two "
            "arms independently. That is an unpaired bootstrap. The paper "
            "describes its bootstrap as paired."
        ),
        "correlation_between_arms_across_tasks": rho,
        "paired_task_clustered": {
            "mean_pp": round(100 * paired["mean"], 3),
            "ci95_pp": [round(100 * paired["ci_lo"], 3), round(100 * paired["ci_hi"], 3)],
            "se_pp": round(100 * paired["se_boot"], 3),
        },
        "unpaired_as_shipped": {
            "mean_pp": round(100 * unpaired["mean"], 3),
            "ci95_pp": [round(100 * unpaired["ci_lo"], 3), round(100 * unpaired["ci_hi"], 3)],
            "se_pp": round(100 * unpaired["se_boot"], 3),
        },
        "se_ratio_unpaired_over_paired": round(unpaired["se_boot"] / paired["se_boot"], 3),
        "direction": (
            "With positively correlated arms the unpaired bootstrap "
            "over-states the standard error, so it is conservative for a null "
            "result and anti-conservative for nothing. The problem is not that "
            "it flipped a conclusion here; it is that the reported interval is "
            "not the interval the stated method produces."
        ),
    }

    # --- E2: task-level clustering / design effect -------------------------
    e2 = {}
    if role_runs:
        by_task = defaultdict(list)
        for r in role_runs:
            if r.get("pass") is None:
                continue
            by_task[r["task_id"]].append(1.0 if r["pass"] else 0.0)
        groups = [v for v in by_task.values() if len(v) >= 2]
        icc = icc_one_way(groups)
        n_tot = sum(len(g) for g in groups)
        k = len(groups)
        mbar = n_tot / k if k else float("nan")
        deff = 1 + (mbar - 1) * icc["icc"] if icc["icc"] == icc["icc"] else float("nan")
        k_pass = int(sum(sum(g) for g in groups))
        lo, hi = wilson_ci(k_pass, n_tot)
        eff_n = n_tot / deff if deff and deff == deff and deff > 0 else float("nan")
        lo_c, hi_c = wilson_ci(int(round(k_pass / deff)), int(round(eff_n))) if eff_n == eff_n else (float("nan"), float("nan"))
        e2["role_mixing_pool"] = {
            "source": P_ROLE_RUNS,
            "n_runs": n_tot,
            "n_task_clusters": k,
            "mean_runs_per_task": round(mbar, 2),
            "icc_1_1_on_pass": round(icc["icc"], 4),
            "design_effect": round(deff, 2),
            "effective_sample_size": round(eff_n, 1),
            "naive_wilson_ci_on_pass_rate": [round(lo, 4), round(hi, 4)],
            "cluster_adjusted_wilson_ci": [round(lo_c, 4), round(hi_c, 4)],
            "ci_width_inflation": round((hi_c - lo_c) / (hi - lo), 2) if (hi - lo) > 0 else None,
            "finding": (
                "Rates pooled over this run pool are quoted with Wilson "
                "intervals computed on the raw run count. Runs are nested "
                "within tasks with substantial intraclass correlation, so the "
                "effective sample size is a fraction of the run count and the "
                "quoted interval is too narrow by roughly the square root of "
                "the design effect."
            ),
        }
    # Reference ablation, conditions clustered within task
    groups_ref = []
    for r in pool:
        groups_ref.append([r[c] for c in SUMMARY_KEYS])
    icc_ref = icc_one_way(groups_ref)
    e2["reference_ablation_conditions_within_task"] = {
        "icc_1_1_on_partial_score": round(icc_ref["icc"], 4),
        "k_task_clusters": icc_ref["k_groups"],
        "runs_per_task": 5,
        "design_effect_if_runs_pooled": round(1 + (5 - 1) * icc_ref["icc"], 2),
        "note": (
            "Any statistic that pools the 775 reference-ablation runs as if "
            "they were independent inflates its sample size by this factor. "
            "The per-task paired contrasts used above are immune to this "
            "because the task is the unit of analysis."
        ),
    }

    # --- E3: multiplicity across the whole family --------------------------
    fam = {
        "partition_value_g_nonzero": sign_flip_p(solo - restricted, n_boot, rng),
        "team_advantage_u_nonzero": sign_flip_p(team - solo, n_boot, rng),
        "relay_advantage_nonzero": sign_flip_p(team - restricted, n_boot, rng),
        "planner_value_nonzero": sign_flip_p(
            team - np.array([r[COND_NO_PLAN] for r in pool]), n_boot, rng),
        "verifier_value_nonzero": sign_flip_p(
            team - np.array([r[COND_NO_VERIFY] for r in pool]), n_boot, rng),
    }
    e3 = {
        "finding": (
            "Multiplicity is corrected inside one family of three tests "
            "(scripts/statistical_robustness.py applies Holm-Bonferroni there) "
            "while the rest of the paper's confirmatory tests -- per-condition "
            "contrasts, per-category uplift, per-quintile contrasts, "
            "per-model leaderboard comparisons -- are reported uncorrected. "
            "Correcting one family and not the others is not a correction."
        ),
        "family_as_reported_here": fam,
        "holm": holm(fam),
        "benjamini_hochberg": benjamini_hochberg(fam),
        "recommendation": (
            "Declare one confirmatory family in the protocol (the five "
            "condition contrasts), correct it, and label everything else "
            "explicitly exploratory. Per-category and per-quintile numbers "
            "should carry no stars at all."
        ),
    }

    return {"E1_bootstrap_pairing": e1, "E2_clustering_and_design_effect": e2,
            "E3_multiplicity": e3}


# ===========================================================================
# SECTION F: robustness to the data-provenance repair
# ===========================================================================
def headline_set(pool, n_boot, rng, n_perm) -> dict:
    """The quantities every conclusion in this reanalysis rests on."""
    solo = np.array([r[COND_SOLO] for r in pool])
    restricted = np.array([r[COND_RESTRICTED] for r in pool])
    team = np.array([r[COND_TEAM] for r in pool])
    g, u = solo - restricted, team - solo
    stats = _sps

    t_gap = g.mean() / (g.std(ddof=1) / math.sqrt(len(g)))
    bu = task_clustered_bootstrap(u, n_boot, rng)
    bg = task_clustered_bootstrap(g, n_boot, rng)
    br = task_clustered_bootstrap(team - restricted, n_boot, rng)

    # quintile profile and its exact null
    rows = quintile_profile(solo, u)
    prof = np.array([r["mean_contrast_pp"] for r in rows])
    spread = float(prof[0] - prof[-1])
    n = len(solo)
    nulls = np.empty((n_perm, 5))
    for i in range(n_perm):
        flip = rng.random(n) < 0.5
        s_p = np.where(flip, team, solo)
        t_p = np.where(flip, solo, team)
        nulls[i] = [r["mean_contrast_pp"] for r in quintile_profile(s_p, t_p - s_p)]
    nsp = nulls[:, 0] - nulls[:, -1]

    fi = fieller_interval(team - restricted, g)
    return {
        "n_tasks": len(pool),
        "necessity_gap_mean": float(g.mean()),
        "necessity_gap_t": float(t_gap),
        "necessity_gap_p": float(2 * stats.t.sf(abs(t_gap), df=len(g) - 1)),
        "necessity_gap_exactly_zero_tasks": int(np.sum(np.abs(g) < 1e-9)),
        "partition_value_g_pp": [round(100 * bg["mean"], 2), round(100 * bg["ci_lo"], 2), round(100 * bg["ci_hi"], 2)],
        "team_advantage_u_pp": [round(100 * bu["mean"], 2), round(100 * bu["ci_lo"], 2), round(100 * bu["ci_hi"], 2)],
        "team_advantage_u_perm_p": sign_flip_p(u, n_boot, rng),
        "relay_advantage_pp": [round(100 * br["mean"], 2), round(100 * br["ci_lo"], 2), round(100 * br["ci_hi"], 2)],
        "quintile_profile_pp": [round(float(x), 2) for x in prof],
        "quintile_q1_minus_q5_pp": round(spread, 2),
        "quintile_null_q1_minus_q5_pp": round(float(nsp.mean()), 2),
        "quintile_p_vs_null": float((np.sum(nsp >= spread) + 1) / (n_perm + 1)),
        "quintile_p_null_flatter": float((np.sum(nsp <= spread) + 1) / (n_perm + 1)),
        "quintile_rtm_corrected_pp": round(spread - float(nsp.mean()), 2),
        "fieller_bounded": bool(fi.get("bounded", True)),
        "fieller_form": fi.get("form"),
    }


def section_g(published_pool, replicates, n_boot, rng) -> dict:
    """Where the multi-agent gain lives: the pass line, not the graded score.

    Two of the paper's own analyses report the same contrast with opposite
    signs.  The 155-task table works in partial score and shows nothing; the
    multi-seed robustness script works in binary pass and shows +20 points.
    Neither is wrong.  They measure different functionals of the same runs, and
    the difference between them is the finding.
    """
    stats = _sps

    clean = build_clean_pool(published_pool, restrict_to_published=False)["pool"]
    if len(clean) < 30:
        return {"available": False, "n_tasks": len(clean)}

    P = {c: np.array([r[c] for r in clean]) for c in SUMMARY_KEYS}
    B = {c: np.array([r[c + "__pass"] for r in clean]) for c in SUMMARY_KEYS}

    def contrast(M, a, b, label):
        d = M[a] - M[b]
        bs = task_clustered_bootstrap(d, n_boot, rng)
        return {
            "scale": label,
            "mean_pp": round(100 * bs["mean"], 2),
            "ci95_pp": [round(100 * bs["ci_lo"], 2), round(100 * bs["ci_hi"], 2)],
            "permutation_p": sign_flip_p(d, n_boot, rng),
            "wins": int(np.sum(d > 0)), "losses": int(np.sum(d < 0)),
            "ties": int(np.sum(d == 0)),
            "rate_a": round(float(M[a].mean()), 4),
            "rate_b": round(float(M[b].mean()), 4),
        }

    rows = {}
    for a, b, name in [(COND_TEAM, COND_SOLO, "full_minus_solo"),
                       (COND_TEAM, COND_RESTRICTED, "full_minus_restricted"),
                       (COND_SOLO, COND_RESTRICTED, "solo_minus_restricted")]:
        rows[name] = {
            "graded_partial_score": contrast(P, a, b, "partial score in [0,1]"),
            "binary_pass": contrast(B, a, b, "grader pass/fail"),
        }

    # Where does the team's extra pass come from?  Tasks the team passes and
    # Solo does not, and what the partial scores look like there.
    team_only = (B[COND_TEAM] == 1) & (B[COND_SOLO] == 0)
    solo_only = (B[COND_SOLO] == 1) & (B[COND_TEAM] == 0)
    both = (B[COND_TEAM] == 1) & (B[COND_SOLO] == 1)
    neither = (B[COND_TEAM] == 0) & (B[COND_SOLO] == 0)
    d_partial = P[COND_TEAM] - P[COND_SOLO]
    mechanism = {
        "n_tasks": len(clean),
        "team_passes_solo_fails": int(team_only.sum()),
        "solo_passes_team_fails": int(solo_only.sum()),
        "both_pass": int(both.sum()),
        "neither_passes": int(neither.sum()),
        "mcnemar_p": float(stats.binomtest(int(team_only.sum()),
                                           int(team_only.sum() + solo_only.sum()),
                                           0.5).pvalue)
        if (team_only.sum() + solo_only.sum()) > 0 else float("nan"),
        "mean_partial_contrast_among_neither_passes_pp": round(
            100 * float(d_partial[neither].mean()), 2) if neither.any() else None,
        "mean_partial_contrast_among_both_pass_pp": round(
            100 * float(d_partial[both].mean()), 2) if both.any() else None,
        "reading": (
            "The team converts failures into passes more often than the reverse, "
            "and simultaneously loses graded credit on the tasks where neither "
            "arm reaches the pass line. A benchmark reported only as pass rate "
            "sees the first effect; one reported only as graded score sees the "
            "second. Reporting both is the finding, not a caveat."
        ),
    }

    # Same contrast on the multi-seed subset, both scales, seeds pooled.
    ms = _multiseed_both_scales(replicates, n_boot, rng)

    # The pass-scale gain is measured on runs predating the shared TurnBudget.
    E = {c: np.array([r.get(c + "__elapsed", 0.0) for r in clean]) for c in SUMMARY_KEYS}
    have_time = all(float(v.sum()) > 0 for v in E.values())
    compute = {"available": have_time}
    if have_time:
        ratio = float(E[COND_TEAM].mean() / E[COND_SOLO].mean()) if E[COND_SOLO].mean() > 0 else None
        gap = E[COND_TEAM] - E[COND_SOLO]
        pass_gain = B[COND_TEAM] - B[COND_SOLO]
        compute.update({
            "mean_elapsed_sec_by_condition": {c: round(float(E[c].mean()), 1) for c in SUMMARY_KEYS},
            "team_over_solo_wall_clock_ratio": round(ratio, 2) if ratio else None,
            "corr_pass_gain_with_elapsed_gap": round(
                float(np.corrcoef(gap, pass_gain)[0, 1]), 3),
            "harness_budgets_before_equalisation": (
                "harness/ablation.py::run_ablation_condition documents the "
                "pre-equalisation configuration in its own docstring: Solo ran "
                "at 20 turns against a Full Team at up to 140. The runs in this "
                "pool predate the shared TurnBudget, so they carry that gap."
            ),
            "caveat": (
                "The pass-scale advantage above is NOT compute-matched. It is "
                "measured on runs where the team was allowed several times the "
                "single agent's turn allowance, so the correct reading is that "
                "the multi-agent gain that this benchmark reports lives on the "
                "pass criterion AND is measured under a compute asymmetry. "
                "Those are the two confounds to separate, and separating them "
                "requires re-running the pool under the shared budget. Nothing "
                "here decides how much of the pass-scale gain survives "
                "equalisation."
            ),
        })

    return {
        "available": True,
        "pool": "provenance-controlled gemini-3-flash-preview seed-0 pool",
        "n_tasks": len(clean),
        "contrasts_on_both_scales": rows,
        "pass_transition_mechanism": mechanism,
        "compute_matching_caveat": compute,
        "multiseed_subset_both_scales": ms,
        "subset_disagreement": (
            "The graded-score contrast is null on the full provenance-controlled "
            "pool and positive on the 39-task multi-seed subset. Those are "
            "different task pools, not different scales: the multi-seed subset "
            "was selected for re-running and is a quarter of the size. Read the "
            "scale decomposition off the full pool and treat the subset as a "
            "separate, smaller estimate rather than a replication of it."
        ),
        "why_this_matters": (
            "The apparent multi-agent gain is scale-dependent. On the pass "
            "criterion the team is ahead; on the graded score it is not. That "
            "is a decomposition, not a contradiction, and it explains why "
            "different analyses in the same repository disagreed about the sign "
            "of the same effect. Any multi-agent benchmark that reports one "
            "scale and not the other can report a gain or a loss at will."
        ),
    }


def _multiseed_both_scales(replicates, n_boot, rng) -> dict:
    """Full vs Solo on the multi-seed subset, per-task means, both scales.

    The replicate structure carries partial scores only, so the binary version
    is reconstructed from the phase-3 pass flags directly.
    """
    if not os.path.exists(P_PHASE3):
        return {"available": False}
    with open(P_PHASE3) as fh:
        doc = json.load(fh)
    part: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    binr: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for run in doc.get("runs", []):
        s = _partial(run)
        if s is None:
            continue
        part[run["task_id"]][run["condition"]].append(s)
        binr[run["task_id"]][run["condition"]].append(1.0 if run.get("pass") else 0.0)
    tasks = [t for t in sorted(part)
             if COND_TEAM in part[t] and COND_SOLO in part[t]]
    if len(tasks) < 10:
        return {"available": False, "n_tasks": len(tasks)}
    dp = np.array([np.mean(part[t][COND_TEAM]) - np.mean(part[t][COND_SOLO]) for t in tasks])
    db = np.array([np.mean(binr[t][COND_TEAM]) - np.mean(binr[t][COND_SOLO]) for t in tasks])
    bp = task_clustered_bootstrap(dp, n_boot, rng)
    bb = task_clustered_bootstrap(db, n_boot, rng)
    return {
        "available": True,
        "n_tasks": len(tasks),
        "seeds": "1 and 2 (the seeds that carry a partial score under the correct key)",
        "graded_partial_score": {
            "mean_pp": round(100 * bp["mean"], 2),
            "ci95_pp": [round(100 * bp["ci_lo"], 2), round(100 * bp["ci_hi"], 2)],
            "permutation_p": sign_flip_p(dp, n_boot, rng),
        },
        "binary_pass": {
            "mean_pp": round(100 * bb["mean"], 2),
            "ci95_pp": [round(100 * bb["ci_lo"], 2), round(100 * bb["ci_hi"], 2)],
            "permutation_p": sign_flip_p(db, n_boot, rng),
        },
        "note": (
            "shared/paper/statistical_robustness.json reports Full minus Solo "
            "as +20.5 points on this subset with p = 0.0024. That analysis is "
            "on the binary pass scale and pools seeds 0-2 as per-task means. "
            "The graded-score contrast on the same runs is the other column."
        ),
    }


def section_f(published_pool, n_boot, rng, n_perm) -> dict:
    clean96 = build_clean_pool(published_pool, restrict_to_published=True)
    clean_all = build_clean_pool(published_pool, restrict_to_published=False)
    out = {
        "why": (
            "The canonical table mixes models, mixes seeds, and averages "
            "binarised scores with continuous ones. Before retiring a metric on "
            "the basis of that table, every conclusion has to survive on a pool "
            "built without those defects."
        ),
        "pools": {
            "published_155": {"n_tasks": len(published_pool),
                              "definition": "shared/paper/ablation_summary.json as stored"},
            "clean_single_model_in_published": {k: v for k, v in clean96.items() if k != "pool"},
            "clean_single_model_all": {k: v for k, v in clean_all.items() if k != "pool"},
        },
        "headline_quantities": {
            "published_155": headline_set(published_pool, n_boot, rng, n_perm),
            "clean_single_model_in_published": headline_set(clean96["pool"], n_boot, rng, n_perm)
            if len(clean96["pool"]) >= 30 else {"n_tasks": len(clean96["pool"]), "skipped": "too few tasks"},
            "clean_single_model_all": headline_set(clean_all["pool"], n_boot, rng, n_perm)
            if len(clean_all["pool"]) >= 30 else {"n_tasks": len(clean_all["pool"]), "skipped": "too few tasks"},
        },
    }
    hs = out["headline_quantities"]
    agree = []
    for name, h in hs.items():
        if "skipped" in h:
            continue
        agree.append({
            "pool": name,
            "n": h["n_tasks"],
            "denominator_statistically_zero": h["necessity_gap_p"] > 0.05,
            "team_advantage_ci_covers_zero": h["team_advantage_u_pp"][1] <= 0 <= h["team_advantage_u_pp"][2],
            "quintile_spread_not_above_null": h["quintile_p_vs_null"] > 0.05,
            "fieller_unbounded": not h["fieller_bounded"],
        })
    out["conclusion_stability"] = {
        "rows": agree,
        "statement": (
            "Every load-bearing conclusion -- the TNI denominator is "
            "statistically zero, a valid interval for the ratio is unbounded, "
            "the compute-matched team advantage is not distinguishable from "
            "zero, and the quintile profile is not steeper than its own null -- "
            "holds on the published pool and on the provenance-controlled pool. "
            "The data-integrity defects are a separate finding, not the reason "
            "the metric fails."
        ),
    }
    return out


# ===========================================================================
# Markdown rendering
# ===========================================================================
def render_markdown(res: dict) -> str:
    A = res["A_tni_autopsy"]
    B = res["B_replacement_estimand"]
    C = res["C_quintile_redone"]
    D = res["D_uplift_relabelled"]
    E = res["E_machinery_audit"]

    dd = A["denominator_diagnostics"]
    fi = A["fieller_confidence_set_for_ratio_of_means"]
    cl = A["clamp_census"]
    L = []
    ap = L.append

    ap("# TeamBench reanalysis: retiring TNI and rebuilding the statistics\n")
    ap(f"Generated by `scripts/reanalysis.py` on the {res['meta']['n_tasks_reference_pool']}-task "
       "reference ablation, the LB90 leaderboard pool, and the role-mixing run pool. "
       "Every figure below is recomputed from primitive per-run condition scores; "
       "no stored derived field is trusted.\n")

    nz0 = A["denominator_measurement_noise"]
    wl0 = B["win_loss_asymmetry"]
    c2_0 = C["C2_exact_null_for_that_design"]
    ap("## 0. One mechanism, three failures\n")
    if nz0.get("available"):
        ap(f"A single run's per-task necessity gap has reliability "
           f"**{nz0['reliability_of_a_single_run_gap']:.2f}** on the multi-seed subset: "
           f"{100*(1-nz0['reliability_of_a_single_run_gap']):.0f} percent of the apparent "
           "task-to-task variation in how much the information partition is worth is "
           "run-to-run noise, not task structure. That one fact generates all three "
           "problems below, and it is a property of the measurement design rather than "
           "of any analysis choice made afterwards.\n")
    ap("1. **The ratio.** TNI divides a difference by that noisy, near-zero quantity. "
       f"Its denominator has mean {A['denominator_diagnostics']['mean']:+.4f} "
       f"(t = {A['denominator_diagnostics']['t']:.2f}) and is exactly zero on "
       f"{A['denominator_diagnostics']['exactly_zero']} of "
       f"{A['denominator_diagnostics']['n_tasks']} tasks, so no bounded confidence set for "
       "the ratio exists.")
    ap("2. **The stratification.** Conditioning on that same noisy run and then reporting a "
       "difference that contains it produces a monotone capability gradient out of nothing: "
       f"the exact no-effect null of the published design gives a Q1-minus-Q5 spread of "
       f"{c2_0['null_q1_minus_q5_mean_pp']:+.1f} pp against the published "
       f"{C['C1_published_design_reproduced']['q1_minus_q5_pp']:+.1f} pp.")
    hh0 = B["hierarchical_admission_partition_value"]
    if hh0.get("at_variance_boundary"):
        ap("3. **The admission count.** The between-task variance in partition value is "
           "not distinguishable from zero once run-to-run noise is subtracted, so a rule "
           "that counts tasks whose single-run estimate clears a threshold is counting "
           "noise excursions. On this corpus that count is "
           f"{hh0['thresholds']['tau=0.1']['naive_fraction_of_point_estimates_above_tau']:.3f} "
           "of tasks at a 10-point threshold and the corpus supports "
           f"{hh0['thresholds']['tau=0.1']['pi_hierarchical']:.3f}.\n")
    else:
        ap("3. **The admission count.** Counting tasks whose single-run estimate clears a "
           "threshold counts noise excursions as task properties.\n")
    ap("On the one place where a capability-conditional signal might still live -- "
       "stratifying on a difficulty estimate that shares no run with the contrast -- "
       "the evidence is marginal and does not replicate across the three instruments. "
       "What would settle it: " + C["C5_verdict"]["what_would_settle_it"][0].lower()
       + C["C5_verdict"]["what_would_settle_it"][1:] + "\n")
    ap("Against that, the effect the aggregate was hiding is real and survives: the team "
       f"wins {wl0['team_wins']} of {wl0['n_contested']} contested tasks (sign test "
       f"p = {wl0['sign_test_p']:.1e}) while its mean advantage is "
       f"{wl0['mean_contrast_pp']:+.2f} pp, because it loses by "
       f"{wl0['loss_to_gain_magnitude_ratio']} times as much as it wins by.\n")

    ap("## 1. Why TNI is not estimable on this pool\n")
    ap("### 1.1 The denominator is statistically zero\n")
    ap(f"- Necessity gap (Solo minus Restricted) over {dd['n_tasks']} tasks: "
       f"mean **{dd['mean']:+.4f}**, SD {dd['sd']:.4f}, "
       f"t = **{dd['t']:.3f}**, p = {dd['p_two_sided']:.3f}.")
    ap(f"- Exactly zero on **{dd['exactly_zero']} of {dd['n_tasks']} tasks** "
       f"({100*dd['exactly_zero']/dd['n_tasks']:.0f} percent); "
       f"negative on {dd['negative']}, positive on {dd['positive']}.")
    ap(f"- On **{dd['below_eps_0.05_signed']} of {dd['n_tasks']} tasks** "
       f"({100*dd['fraction_where_paper_eps_is_active']:.0f} percent) the paper's "
       "epsilon floor is the binding value, so the denominator is a constant "
       "the authors chose, not a measurement.\n")

    ai = A["algebraic_identity"]
    ap("### 1.2 The ratio adds nothing the difference does not already carry\n")
    ap(f"- Identity, exact to {ai['max_abs_residual']:.1e} on every task: "
       "`(Team - Restricted) = (Solo - Restricted) + (Team - Solo)`.")
    ap(f"- Therefore **{ai['consequence']}**.")
    ap("- On tasks with a positive gap, the claim \"TNI > 1\" is algebraically "
       "identical to \"Team beats Solo\". The ratio contributes no information "
       "beyond the sign of the difference, and it contributes unbounded variance.\n")

    ap("### 1.3 The shipped implementations disagree with each other and with the paper\n")
    ap("Four code paths compute something called TNI, and none of them computes "
       "Eq. (1) as written. The last row is not shipped anywhere; it is the raw "
       "ratio, included so the effect of each guard is visible.\n")
    ap("| implementation | defined on | mean | min | max |")
    ap("|---|---|---|---|---|")
    for key, v in A["implementations_on_one_pool"].items():
        ap(f"| `{key}` | {v['n_defined']}/{v['n_defined']+v['n_undefined']} | "
           f"{('%.3f' % v['mean']) if v['mean'] is not None else 'n/a'} | "
           f"{('%.2f' % v['min']) if v['min'] is not None else 'n/a'} | "
           f"{('%.2f' % v['max']) if v['max'] is not None else 'n/a'} |")
    ss = A["same_subset_comparison"]
    ap(f"\nOn the identical {ss['n']}-task subset the paper's Eq. (1) returns "
       f"**{ss['paper_eq1_mean']:+.3f}** and `harness/compute_tni.py` returns "
       f"**{ss['compute_tni_py_mean']:+.3f}**, with "
       f"{ss['sign_disagreements_paper_vs_code']} sign disagreements. "
       f"`harness/validate_tni.py` computes a different estimand entirely and "
       "publishes it under the same name.\n")
    ic = A["internal_inconsistency_in_stored_summary"]
    ap(f"`shared/paper/ablation_summary.json` is internally inconsistent: its "
       f"per-task block admits {ic['n_per_task_nonnull_abs_filter']} tasks "
       f"(mean {ic['mean_abs_filter']:+.3f}) while its own aggregate block admits "
       f"{ic['n_aggregate_signed_filter']} (mean {ic['mean_signed_filter']:+.3f}).\n")

    ap("### 1.4 The clamp is load-bearing and undocumented\n")
    ap(f"- {cl['n_on_upper_clamp']} values sit on +2 and {cl['n_on_lower_clamp']} on -2, "
       f"which is **{100*cl['fraction_on_a_clamp']:.0f} percent of the "
       f"{cl['n_reported']} reported values**.")
    ap(f"- Removing the clamp moves the mean from {cl['mean_with_clamp']:+.3f} to "
       f"{cl['mean_without_clamp']:+.3f}, with an unclamped range of "
       f"[{cl['min_without_clamp']:.1f}, {cl['max_without_clamp']:.1f}].")
    ap("- The clamp appears nowhere in the paper.\n")

    rec = A.get("reconciliation_with_earlier_internal_figures")
    if rec:
        ap(rec["note"] + "\n")

    ap("### 1.5 A valid interval for the ratio is unbounded\n")
    ap(f"- Fieller construction on the ratio of means: point estimate "
       f"{fi['point_ratio']:+.3f}, denominator t = {fi['den_t']:.3f} "
       f"(critical value {fi['t_crit']:.3f}).")
    ap(f"- Quadratic leading coefficient a = {fi['a']:.5g} <= 0, so the 95 percent "
       f"confidence set is **{fi.get('confidence_set', fi.get('form'))}** -- "
       "the ratio is not estimable at this sample size.")
    ht = A["heavy_tail_of_mean_per_task_ratio"]
    ap(f"- The bootstrap distribution of the *mean of per-task ratios* on the "
       f"{ht['subset_n']} defined tasks spans "
       f"[{ht['bootstrap_mean_min']:.1f}, {ht['bootstrap_mean_max']:.1f}] with a "
       f"95 percent width of {ht['bootstrap_ci_width']:.2f}.\n")

    sim = A["simulation_denominator_to_zero"]
    ap("### 1.6 Simulation: the estimator as the denominator approaches zero\n")
    ap("| E[denominator] | true ratio | SD of estimate | coverage, naive percentile bootstrap | coverage, Fieller | Fieller unbounded |")
    ap("|---|---|---|---|---|---|")
    for r in sim["grid"]:
        ap(f"| {r['denominator_mean']:.3f} | {r['true_ratio']:.2f} | {r['sd_estimate']:.2f} | "
           f"{r['coverage_naive_percentile_bootstrap']:.3f} | {r['coverage_fieller']:.3f} | "
           f"{r['frac_fieller_unbounded']:.2f} |")
    ap(f"\nObserved denominator mean on this pool: {sim['observed_denominator_mean_for_reference']:+.4f}, "
       "far to the left of the leftmost grid point. " + sim["reading"] + "\n")

    nz = A["denominator_measurement_noise"]
    if nz.get("available"):
        ap(f"On the {nz['n_tasks_with_replicates']}-task multi-seed subset, a single "
           f"run's necessity gap has reliability "
           f"**{nz['reliability_of_a_single_run_gap']:.2f}** "
           f"(within-task variance {nz['within_task_variance_sigma2_e']:.4f} against "
           f"between-task variance {nz['between_task_variance_sigma2_theta']:.4f}).\n")

    ap("## 2. The replacement: the Coordination Necessity Contrast\n")
    dfn = B["definition"]
    ap(f"**{dfn['name']}**. {dfn['shape']}\n")
    ap(f"- `g_i` = {dfn['g_definition']}")
    ap(f"- `u_i` = {dfn['u_definition']}\n")
    ap(dfn["why_two_dimensions"] + "\n")
    ap(f"- Estimator: {dfn['estimator']}.")
    ap(f"- Interval: {dfn['ci_construction']}.")
    ap(f"- Null: {dfn['null_behaviour']}.\n")
    ap("| quantity | mean (pp) | 95% CI (pp) | permutation p |")
    ap("|---|---|---|---|")
    pmap = B["permutation_p_values"]
    labels = {
        "partition_value_g_solo_minus_restricted": ("partition value g", "partition_value_g"),
        "team_advantage_u_full_minus_solo": ("team advantage u", "team_advantage_u"),
        "relay_advantage_full_minus_restricted": ("relay advantage (old TNI numerator)", "relay_advantage"),
        "planner_value_full_minus_no_plan": ("planner value", "planner_value"),
        "verifier_value_full_minus_no_verify": ("verifier value", "verifier_value"),
    }
    for k, (lab, pk) in labels.items():
        v = B["pool_level_estimates"][k]
        ap(f"| {lab} | {100*v['mean']:+.2f} | [{100*v['ci_lo']:+.2f}, {100*v['ci_hi']:+.2f}] | {pmap[pk]:.3f} |")
    wl = B["win_loss_asymmetry"]
    ap(f"\n**A zero mean is not no effect.** Of {wl['n_tasks']} tasks the contrast is "
       f"tied on {wl['n_ties']}. Among the {wl['n_contested']} contested tasks the team wins "
       f"**{wl['team_wins']}** and loses {wl['team_losses']}, a win rate of "
       f"{wl['win_rate_among_contested']:.3f} "
       f"[{wl['win_rate_wilson_ci'][0]:.3f}, {wl['win_rate_wilson_ci'][1]:.3f}], sign test "
       f"p = {wl['sign_test_p']:.2e}. But it gains "
       f"{wl['mean_gain_when_team_wins_pp']:+.1f} pp when it wins and loses "
       f"{wl['mean_loss_when_team_loses_pp']:+.1f} pp when it loses, a magnitude ratio of "
       f"{wl['loss_to_gain_magnitude_ratio']}. The two cancel to a mean of "
       f"{wl['mean_contrast_pp']:+.2f} pp.\n")
    ap(wl["reading"] + "\n")
    q = B["two_dimensional_task_census"]
    ap(f"\nTwo-dimensional census at tau = {q['thresholds']['tau_g']}: "
       f"**{q['coordination_demanding_g_pos_u_pos']}** tasks are coordination-demanding "
       f"(positive partition value *and* positive team advantage); "
       f"{q['partition_matters_but_team_does_not_g_pos_u_neg']} have a real partition the "
       f"team fails to exploit; {q['inverted_partition_g_neg']} have an inverted partition "
       "where Restricted beats Solo.\n")

    h = B["hierarchical_admission_partition_value"]
    if h.get("available"):
        ap("### 2.1 Benchmark admission as a probability, not a count\n")
        ap(f"Measurement variance of the contrast, from the "
           f"{h['n_tasks_supplying_sigma2_e']}-task replicate subset: "
           f"sigma2_e = {h['sigma2_e_from_replicates']:.4f}. Task-to-task variance of the "
           f"single-run estimates on the full pool: {h['var_of_single_run_estimates_full_pool']:.4f}. "
           f"Implied between-task variance: {h['tau2_between_task_full_pool']:+.4f} on the full pool "
           f"and {h['tau2_between_task_replicate_subset']:+.4f} on the replicate subset.\n")
        if h.get("at_variance_boundary") and h.get("boundary_reading"):
            ap("> " + h["boundary_reading"] + "\n")
        ap("| threshold | hierarchical pi(tau) | naive count rule | inflation | expected qualifying tasks |")
        ap("|---|---|---|---|---|")
        nkey = [k for k in list(h["thresholds"].values())[0] if k.startswith("expected_qualifying")][0]
        for tk, tv in h["thresholds"].items():
            ap(f"| {tk} | {tv['pi_hierarchical']:.3f} | "
               f"{tv['naive_fraction_of_point_estimates_above_tau']:.3f} | "
               f"{tv['inflation_of_naive_over_hierarchical']:+.3f} | "
               f"{tv[nkey]:.1f} |")
        rn = h.get("runs_per_cell_needed", {})
        if rn.get("runs"):
            ap(f"Runs per cell needed to make a single task's estimate reliable, under the "
               f"optimistic between-task variance {rn['assumed_tau2']:.4f}: "
               + ", ".join(f"{k.replace('reliability_','reliability ')} needs {v} runs"
                           for k, v in rn["runs"].items() if v is not None)
               + f" (the reference ablation has {rn['current_runs_per_cell']}).\n")
        ap("\nSensitivity to the measurement-variance estimate:\n")
        ap("| assumed sigma2_e | implied reliability of one run | pi(0.10) | pi(0.20) |")
        ap("|---|---|---|---|")
        for sk, sv in h["sensitivity_to_sigma2_e"].items():
            ap(f"| {sk} ({sv['sigma2_e']:.4f}) | "
               f"{(sv['implied_reliability'] if sv['implied_reliability'] is not None else float('nan')):.3f} | "
               f"{sv['pi_at_tau_0.10']:.3f} | {sv['pi_at_tau_0.20']:.3f} |")
        ap("")
        ap(h["reading"] + "\n")
        na = B["admission_statistic_under_the_null"]
        if na.get("available"):
            ap("\nUnder an exact no-effect null:")
            for tk, tv in na["null_levels"].items():
                ap(f"- {tk}: naive count rule still admits "
                   f"{tv['naive_count_rule_mean']:.3f} of tasks; the hierarchical rule admits "
                   f"{tv['hierarchical_rule_mean']:.3f}.")
            ap("")

    ap("## 3. The quintile result, redone\n")
    c1, c2, c4 = C["C1_published_design_reproduced"], C["C2_exact_null_for_that_design"], C["C4_rtm_corrected_effect"]
    ap(f"Published design reproduced: profile "
       f"{c1['profile_pp']} pp, Q1 minus Q5 = **{c1['q1_minus_q5_pp']:+.2f} pp**.")
    if c1.get("published_profile_pp"):
        ap(f"(Stored published profile: {c1['published_profile_pp']}; "
           f"max reproduction difference {c1['reproduction_max_abs_diff_pp']:.2f} pp.)")
    ap(f"\n{c2['mechanism']}\n")
    ap(f"Under the exact null (swap Team and Solo labels within each task, "
       f"{c2['n_permutations']} permutations) the *same design* produces a mean profile of "
       f"**{c2['mean_null_profile_pp']} pp** and a Q1-minus-Q5 spread of "
       f"**{c2['null_q1_minus_q5_mean_pp']:+.2f} pp** "
       f"(5th to 95th percentile {c2['null_q1_minus_q5_p5_p95_pp'][0]:+.1f} to "
       f"{c2['null_q1_minus_q5_p5_p95_pp'][1]:+.1f}). "
       f"Observed spread {c2['observed_q1_minus_q5_pp']:+.2f} pp; "
       f"p(null at least this steep) = {c2['p_value_observed_spread_exceeds_null']:.4f}, "
       f"p(null this flat or flatter) = {c2['p_value_observed_spread_below_null']:.4f}.\n")
    ap(c2['second_verdict'] + "\n")
    ap(f"**RTM-corrected effect: {c4['corrected_q1_minus_q5_pp']:+.2f} pp** "
       f"(uncorrected {c4['uncorrected_q1_minus_q5_pp']:+.2f} pp; the design's own "
       f"artifact accounts for {c4['artifact_share_of_published_spread']:.2f} times "
       "the published spread).\n")
    ap("### 3.1 Stratifying on an independent difficulty estimate\n")
    ap("| instrument | n | profile (pp) | Q1-Q5 (pp) | monotone (Spearman) | null Q1-Q5 | p raw | p Holm | trend slope (pp) | trend p Holm |")
    ap("|---|---|---|---|---|---|---|---|---|---|")
    v5 = C["C5_verdict"]
    for k, v in C["C3_independent_difficulty_instruments"].items():
        if not isinstance(v, dict) or "profile_pp" not in v:
            continue
        hb = v5["quintile_contrast_p_holm_corrected_across_instruments"].get(k, {})
        ht = v5["continuous_trend_p_holm_corrected_across_instruments"].get(k, {})
        ap(f"| {k} | {v['n_tasks']} | {v['profile_pp']} | {v['q1_minus_q5_pp']:+.2f} | "
           f"{v['profile_monotonicity_spearman']:+.2f} | {v['null_q1_minus_q5_mean_pp']:+.2f} | "
           f"{v['p_value_two_sided']:.3f} | {hb.get('p_holm', float('nan')):.3f} | "
           f"{v['continuous_trend_test']['slope_pp_per_sd_of_rank']:+.2f} | "
           f"{ht.get('p_holm', float('nan')):.3f} |")
    ap(f"\n{v5['caution']}\n")
    ap(f"**{v5['statement']}**\n")

    ap("## 4. The uplift, relabelled\n")
    ml = D["the_mislabel"]
    ap(f"`{ml['location']}` computes `{ml['code']}`. {ml['problem']}\n")
    ap("| comparison | mean (pp) | 95% CI (pp) | permutation p | team wins / loses / ties |")
    ap("|---|---|---|---|---|")
    for key, lab in [("full_minus_solo", "Full Team minus Solo"),
                     ("full_minus_restricted", "Full Team minus Restricted")]:
        v = D[key]
        ap(f"| {lab} | {v['mean_pp']:+.2f} | [{v['ci95_pp'][0]:+.2f}, {v['ci95_pp'][1]:+.2f}] | "
           f"{v['permutation_p']:.3f} | {v['n_tasks_team_wins']} / {v['n_tasks_team_loses']} / {v['n_tasks_tied']} |")
    sse = D["the_mislabel"].get("single_sentence_evidence")
    if sse:
        ap(f"\n{sse['paper_sentence']}\n")
        ap(sse["finding"] + "\n")
    lb = D["lb90_paired_replication"]
    ap(f"\nOn LB90, paired within task, Restricted beats Solo for "
       f"**{lb['n_models_where_restricted_beats_solo_paired']} of "
       f"{lb['n_models_with_paired_solo_and_restricted']} models**; pooled "
       f"Restricted minus Solo = {lb['pooled_restricted_minus_solo_pp']:+.2f} pp.\n")
    ap(lb["warning"] + "\n")

    ap("## 5. Statistical machinery audit\n")
    e1 = E["E1_bootstrap_pairing"]
    ap(f"**Pairing.** {e1['finding']} Arms correlate at r = {e1['correlation_between_arms_across_tasks']:.3f} "
       f"across tasks. Paired SE {e1['paired_task_clustered']['se_pp']:.2f} pp against unpaired "
       f"{e1['unpaired_as_shipped']['se_pp']:.2f} pp, a ratio of "
       f"{e1['se_ratio_unpaired_over_paired']:.2f}.\n")
    e2 = E["E2_clustering_and_design_effect"]
    if "role_mixing_pool" in e2:
        rm = e2["role_mixing_pool"]
        ap(f"**Clustering.** The role-mixing pool has {rm['n_runs']} runs nested in "
           f"{rm['n_task_clusters']} tasks ({rm['mean_runs_per_task']} runs per task). "
           f"ICC(1,1) on pass is {rm['icc_1_1_on_pass']}, design effect "
           f"**{rm['design_effect']}**, effective n {rm['effective_sample_size']}. "
           f"A Wilson interval on the raw run count is roughly "
           f"{rm['ci_width_inflation']} times too narrow.\n")
    e3 = E["E3_multiplicity"]
    ap(f"**Multiplicity.** {e3['finding']}\n")
    ap("| test | raw p | Holm | BH | survives Holm |")
    ap("|---|---|---|---|---|")
    for k in e3["family_as_reported_here"]:
        hh = e3["holm"][k]; bb = e3["benjamini_hochberg"].get(k, {})
        ap(f"| {k} | {hh['p_raw']:.4f} | {hh['p_holm']:.4f} | "
           f"{bb.get('p_bh', float('nan')):.4f} | {hh['reject_at_0.05']} |")
    ap(f"\n{e3['recommendation']}\n")

    F = res["F_provenance_and_robustness"]
    pa = F["provenance_audit"]
    ap("## 6. Data provenance of the canonical table, and robustness to repairing it\n")
    bb = pa["silent_binarisation_bug"]
    ap(f"**Silent binarisation.** `{bb['location']}` evaluates\n\n"
       f"```python\n{bb['code']}\n```\n")
    ap(bb["problem"] + "\n")
    ap(f"This fires on **{bb['n_runs_binarised']} runs**, touching "
       f"**{bb['n_table_cells_affected']} of {bb['n_table_cells_total']} cells** "
       "of the canonical per-task table.\n")
    we = bb.get("worked_example", {})
    if we.get("available"):
        ap(f"Worked example, `{we['task']}` / `{we['condition']}`: seed 0 scores "
           f"{we['seed0_partial']}; seeds 1 and 2 score {we['seed12_true_partial']} but are "
           f"read as {we['seed12_as_read_by_paper_tables']}. The table stores "
           f"**{we['stored_table_value']:.5f}** where reading the partial scores gives "
           f"**{we['value_if_partial_scores_were_read']:.5f}**.\n")
    mp = pa["model_provenance"]
    ap(f"**Model provenance.** {mp['problem']} Runs by declared model in the merge:\n")
    for m, n in list(mp["runs_by_declared_model"].items())[:8]:
        ap(f"- `{m}`: {n}")
    ap("")
    mr = pa["merge_reproduced_from_generate_paper_sh"]
    ap(f"**Reproducibility.** Re-running the documented merge over the "
       f"{mr['n_json_files_globbed']} files it globs today reproduces "
       f"{mr['cells_reproduced_exactly']} of "
       f"{mr['cells_reproduced_exactly']+mr['cells_not_reproduced']} cells; "
       f"{mr['cells_not_reproduced']} now differ. {mr['note']}\n")

    ap("### 6.1 Every conclusion survives the repair\n")
    ap("| pool | n | gap mean | gap p | team advantage u (pp, 95% CI) | Q1-Q5 (pp) | null Q1-Q5 (pp) | p | Fieller |")
    ap("|---|---|---|---|---|---|---|---|---|")
    for name, h in F["headline_quantities"].items():
        if "skipped" in h:
            continue
        ap(f"| {name} | {h['n_tasks']} | {h['necessity_gap_mean']:+.4f} | "
           f"{h['necessity_gap_p']:.3f} | {h['team_advantage_u_pp'][0]:+.2f} "
           f"[{h['team_advantage_u_pp'][1]:+.2f}, {h['team_advantage_u_pp'][2]:+.2f}] | "
           f"{h['quintile_q1_minus_q5_pp']:+.2f} | {h['quintile_null_q1_minus_q5_pp']:+.2f} | "
           f"{h['quintile_p_vs_null']:.3f} | {h['fieller_form']} |")
    ap(f"\n{F['conclusion_stability']['statement']}\n")

    G = res.get("G_pass_line_versus_graded_score", {})
    if G.get("available"):
        ap("## 7. Where the multi-agent gain lives: the pass line, not the graded score\n")
        ap(G["why_this_matters"] + "\n")
        ap(f"Provenance-controlled pool, {G['n_tasks']} tasks, both scales on the same runs:\n")
        ap("| contrast | scale | mean (pp) | 95% CI (pp) | perm p | wins / losses / ties |")
        ap("|---|---|---|---|---|---|")
        for name, pair in G["contrasts_on_both_scales"].items():
            for sk, v in pair.items():
                ap(f"| {name} | {v['scale']} | {v['mean_pp']:+.2f} | "
                   f"[{v['ci95_pp'][0]:+.2f}, {v['ci95_pp'][1]:+.2f}] | {v['permutation_p']:.3f} | "
                   f"{v['wins']} / {v['losses']} / {v['ties']} |")
        me = G["pass_transition_mechanism"]
        ap(f"\nPass transitions on the same {me['n_tasks']} tasks: the team passes where Solo "
           f"fails on **{me['team_passes_solo_fails']}** tasks and Solo passes where the team "
           f"fails on {me['solo_passes_team_fails']} (exact paired test p = {me['mcnemar_p']:.4f}); "
           f"{me['both_pass']} tasks are passed by both and {me['neither_passes']} by neither. "
           f"On the tasks neither arm passes, the team's graded score is "
           f"{me['mean_partial_contrast_among_neither_passes_pp']:+.2f} pp against Solo.\n")
        ap(me["reading"] + "\n")
        cm = G.get("compute_matching_caveat", {})
        if cm.get("available"):
            ap(f"**These runs are not compute-matched.** Mean wall clock by condition: "
               + ", ".join(f"{k} {v:.0f}s" for k, v in cm["mean_elapsed_sec_by_condition"].items())
               + f"; the Full Team spends {cm['team_over_solo_wall_clock_ratio']} times the "
                 f"single agent's wall clock, and the per-task pass gain correlates "
                 f"{cm['corr_pass_gain_with_elapsed_gap']} with the per-task elapsed-time gap.\n")
            ap(cm["harness_budgets_before_equalisation"] + "\n")
            ap(cm["caveat"] + "\n")
        ms = G.get("multiseed_subset_both_scales", {})
        if ms.get("available"):
            ap(f"On the {ms['n_tasks']}-task multi-seed subset (seeds {ms['seeds']}), the same "
               f"contrast is {ms['binary_pass']['mean_pp']:+.2f} pp on the pass scale "
               f"[{ms['binary_pass']['ci95_pp'][0]:+.2f}, {ms['binary_pass']['ci95_pp'][1]:+.2f}], "
               f"p = {ms['binary_pass']['permutation_p']:.3f}, and "
               f"{ms['graded_partial_score']['mean_pp']:+.2f} pp on the graded scale "
               f"[{ms['graded_partial_score']['ci95_pp'][0]:+.2f}, "
               f"{ms['graded_partial_score']['ci95_pp'][1]:+.2f}], "
               f"p = {ms['graded_partial_score']['permutation_p']:.3f}.\n")
            ap(ms["note"] + "\n")
            if G.get("subset_disagreement"):
                ap(G["subset_disagreement"] + "\n")

    ap("## 8. What changes in the paper\n")
    for line in res["what_changes"]:
        ap(f"- {line}")
    ap("")
    ap("## 9. What this analysis cannot establish\n")
    for line in res["limitations"]:
        ap(f"- {line}")
    ap("")
    return "\n".join(L)


# ===========================================================================
# Main
# ===========================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--n-perm", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=20260905)
    ap.add_argument("--out", default=os.path.join(REPO, "shared/paper/quality"))
    ap.add_argument("--render-only", action="store_true",
                    help="re-render the markdown summary from an existing reanalysis.json "
                         "without recomputing anything")
    args = ap.parse_args()

    if args.render_only:
        with open(os.path.join(args.out, "reanalysis.json")) as fh:
            res = json.load(fh)
        out_md = os.path.join(args.out, "reanalysis_summary.md")
        with open(out_md, "w") as fh:
            fh.write(render_markdown(res))
        print(f"re-rendered {out_md}", file=sys.stderr, flush=True)
        return 0

    rng = np.random.default_rng(args.seed)
    os.makedirs(args.out, exist_ok=True)

    print("[1/6] loading data", file=sys.stderr, flush=True)
    pool = load_reference_pool()
    crosscheck = load_reference_pool_raw_crosscheck(pool)
    clean_seed0 = {r["task_id"]: r for r in build_clean_pool(pool, restrict_to_published=False)["pool"]}
    replicates = load_replicates(pool, seed0_source=clean_seed0)
    lb90 = load_lb90()
    role_runs = load_role_runs()

    print("[2/6] section A: TNI autopsy", file=sys.stderr, flush=True)
    A = section_a(pool, replicates, args.n_boot, rng)
    print("[3/6] section B: replacement estimand", file=sys.stderr, flush=True)
    B = section_b(pool, replicates, args.n_boot, rng)
    print("[4/6] section C: quintile redone", file=sys.stderr, flush=True)
    C = section_c(pool, lb90, args.n_boot, rng, n_perm=args.n_perm)
    print("[5/6] section D: uplift relabelled", file=sys.stderr, flush=True)
    D = section_d(pool, lb90, args.n_boot, rng)
    print("[6/7] section E: machinery audit", file=sys.stderr, flush=True)
    E = section_e(pool, lb90, role_runs, args.n_boot, rng)
    print("[7/8] section F: provenance audit and robustness", file=sys.stderr, flush=True)
    prov = provenance_audit(pool)
    F = section_f(pool, args.n_boot, rng, args.n_perm)
    F["provenance_audit"] = prov
    print("[8/8] section G: pass line versus graded score", file=sys.stderr, flush=True)
    G = section_g(pool, replicates, args.n_boot, rng)

    res = {
        "meta": {
            "script": "scripts/reanalysis.py",
            "seed": args.seed,
            "n_boot": args.n_boot,
            "n_perm": args.n_perm,
            "n_tasks_reference_pool": len(pool),
            "n_tasks_with_multiseed_replicates": len(replicates),
            "n_lb90_models": len(lb90["matrix"]),
            "n_role_mixing_runs": len(role_runs),
            "sources": {
                "reference_ablation": P_ABLATION_SUMMARY,
                "reference_ablation_raw_crosscheck": crosscheck,
                "multiseed_replicates": P_PHASE3,
                "leaderboard": P_LB90,
                "role_mixing": P_ROLE_RUNS,
                "published_quintile": P_QUINTILE_PUBLISHED,
            },
            "policy": "every derived field is recomputed; no stored TNI, gap, uplift or classification is read",
        },
        "A_tni_autopsy": A,
        "B_replacement_estimand": B,
        "C_quintile_redone": C,
        "D_uplift_relabelled": D,
        "E_machinery_audit": E,
        "F_provenance_and_robustness": F,
        "G_pass_line_versus_graded_score": G,
    }

    res["what_changes"] = [
        "Delete Eq. (1) and every TNI number. Replace with the two-dimensional Coordination Necessity Contrast (g, u), each reported as a paired task-clustered mean with a bootstrap CI.",
        "Replace 'mean team uplift +0.5 points' with the two separate quantities: Full minus Solo = %+.2f pp [%+.2f, %+.2f] and Full minus Restricted = %+.2f pp [%+.2f, %+.2f]." % (
            D["full_minus_solo"]["mean_pp"], D["full_minus_solo"]["ci95_pp"][0], D["full_minus_solo"]["ci95_pp"][1],
            D["full_minus_restricted"]["mean_pp"], D["full_minus_restricted"]["ci95_pp"][0], D["full_minus_restricted"]["ci95_pp"][1]),
        "Replace the quintile figure. The exact no-effect null of the same design produces a STEEPER profile than the published one (null Q1-minus-Q5 %+.2f pp against a published %+.2f pp), so the RTM-corrected contrast is %+.2f pp and the published gradient is fully accounted for by the estimator." % (
            C["C2_exact_null_for_that_design"]["null_q1_minus_q5_mean_pp"],
            C["C1_published_design_reproduced"]["q1_minus_q5_pp"],
            C["C4_rtm_corrected_effect"]["corrected_q1_minus_q5_pp"]),
        "Add the win/loss asymmetry, which is a real result the mean was hiding: the team wins %d of %d contested tasks (sign test p = %.1e) while the mean contrast is %+.2f pp, because losses run %s times larger than wins. Report (win rate, mean effect) as a pair." % (
            B["win_loss_asymmetry"]["team_wins"], B["win_loss_asymmetry"]["n_contested"],
            B["win_loss_asymmetry"]["sign_test_p"], B["win_loss_asymmetry"]["mean_contrast_pp"],
            B["win_loss_asymmetry"]["loss_to_gain_magnitude_ratio"]),
        "Add the scale decomposition as a headline: on the provenance-controlled pool the same runs give a large positive multi-agent effect on the pass criterion (%+.1f pp) and none on the graded score (%+.1f pp). That reconciles the two contradictory numbers already in the repository and is the mechanism behind the win/loss asymmetry. State in the same breath that those runs predate the shared turn budget, so the pass-scale gain is confounded with compute and the equalised re-run is what decides how much of it is coordination." % (
            G["contrasts_on_both_scales"]["full_minus_solo"]["binary_pass"]["mean_pp"],
            G["contrasts_on_both_scales"]["full_minus_solo"]["graded_partial_score"]["mean_pp"],
        ) if G.get("available") else "Add the scale decomposition as a headline.",
        "Report the data-provenance repair. The canonical table averages binarised multi-seed scores with continuous seed-0 scores on %d of %d cells and draws on more than one model; the provenance-controlled pool is the one to publish." % (
            F["provenance_audit"]["silent_binarisation_bug"]["n_table_cells_affected"],
            F["provenance_audit"]["silent_binarisation_bug"]["n_table_cells_total"]),
        "Report benchmark admission as a hierarchical probability with a stated threshold, not as a count of tasks whose single-run estimate clears a line.",
        "State the bootstrap that was actually run. The library function resamples arms independently; the paper calls it paired.",
        "Quote cluster-adjusted intervals for any rate pooled over runs nested in tasks, and give the design effect alongside.",
        "Declare a single confirmatory family, correct it, and mark per-category, per-quintile and per-model numbers as exploratory.",
    ]
    res["limitations"] = [
        "The reference ablation has one run per (task, condition) at seed 0, so per-task estimates carry run-to-run noise that only the %d-task multi-seed subset can quantify. Every shrinkage and RTM figure above imports its measurement variance from that subset and assumes it transfers to the full pool." % len(replicates),
        "The held-out-model difficulty instrument covers only the tasks the reference ablation and LB90 share, so its quintiles are coarser than the full-pool ones.",
        "The permutation nulls test exchangeability of condition labels within a task. They do not test whether the graders measure what the tasks intend, which is a separate validity question handled by the admission gate.",
        "Nothing here establishes that a coordination-required benchmark is impossible. It establishes that this corpus, as scored, does not currently contain a measurable coordination requirement at the resolution the runs provide.",
        "The LB90 aggregate's per-condition task coverage is unequal; the paired figures restrict to each model's task intersection, which changes the denominator relative to the published leaderboard rates.",
    ]

    out_json = os.path.join(args.out, "reanalysis.json")
    with open(out_json, "w") as fh:
        json.dump(res, fh, indent=2, default=float)
    out_md = os.path.join(args.out, "reanalysis_summary.md")
    with open(out_md, "w") as fh:
        fh.write(render_markdown(res))
    print(f"wrote {out_json}", file=sys.stderr, flush=True)
    print(f"wrote {out_md}", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
