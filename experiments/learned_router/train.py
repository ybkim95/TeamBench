#!/usr/bin/env python3
"""
Learned topology router: predict per-task best condition from metadata.

Reads:
  shared/paper/task_regression_data.csv

Reconstructs the four candidate conditions per task from available columns:
    full          = csv['full']
    oracle        = csv['oracle']
    team_no_plan  = csv['full'] - csv['plan_value']
    team_no_verify= csv['full'] - csv['verify_value']
Picks argmax as the oracle-optimal policy per task.

Trains leave-one-category-out logistic regression over (category, difficulty,
is_adversarial, is_multi_lang, log1p(spec_words)) and compares mean uplift vs.
static "always full" baseline.

Writes:
  shared/paper/learned_router_results.json
  shared/paper/table_learned_router.tex
"""
from __future__ import annotations
import csv
import json
import math
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "shared" / "paper" / "task_regression_data.csv"


def load_rows():
    with CSV_PATH.open() as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            try:
                oracle = float(r["oracle"])
                full = float(r["full"])
                pv = float(r["plan_value"])
                vv = float(r["verify_value"])
            except (ValueError, KeyError):
                continue
            rows.append({
                "task_id": r["task_id"],
                "category": r.get("category", "unknown"),
                "difficulty": int(r.get("difficulty", 1)),
                "is_adversarial": int(r.get("is_adversarial", 0)),
                "is_multi_lang": int(r.get("is_multi_lang", 0)),
                "spec_words": float(r.get("spec_words", 0.0) or 0.0),
                "scores": {
                    "oracle": oracle,
                    "full": full,
                    "team_no_plan": full - pv,
                    "team_no_verify": full - vv,
                },
            })
    return rows


CONDITIONS = ["oracle", "full", "team_no_plan", "team_no_verify"]


def oracle_policy(rows):
    """Upper bound: pick argmax per task."""
    picks = []
    for r in rows:
        best = max(CONDITIONS, key=lambda c: r["scores"][c])
        picks.append(best)
    return picks


def static_policy(rows, cond: str):
    return [cond] * len(rows)


def policy_score(rows, policy):
    return float(np.mean([r["scores"][p] for r, p in zip(rows, policy)]))


def build_features(rows):
    cats = np.array([[r["category"]] for r in rows])
    enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    cat_onehot = enc.fit_transform(cats)
    numeric = np.array([
        [r["difficulty"], r["is_adversarial"], r["is_multi_lang"], math.log1p(r["spec_words"])]
        for r in rows
    ], dtype=float)
    X = np.hstack([cat_onehot, numeric])
    return X, enc


def leave_one_category_out(rows):
    X, enc = build_features(rows)
    y = np.array(oracle_policy(rows))
    cats = np.array([r["category"] for r in rows])
    preds = np.empty_like(y)
    for held in np.unique(cats):
        mask_train = cats != held
        mask_test = cats == held
        if len(np.unique(y[mask_train])) < 2:
            preds[mask_test] = "full"
            continue
        clf = LogisticRegression(max_iter=2000)
        clf.fit(X[mask_train], y[mask_train])
        preds[mask_test] = clf.predict(X[mask_test])
    return preds.tolist()


def bootstrap_delta(scores_a, scores_b, n_boot=2000, seed=42):
    rng = np.random.default_rng(seed)
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)
    deltas = np.empty(n_boot)
    n = len(a)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        deltas[i] = a[idx].mean() - b[idx].mean()
    return float(deltas.mean()), float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))


def main() -> int:
    rows = load_rows()
    n = len(rows)
    oracle_pol = oracle_policy(rows)
    learned_pol = leave_one_category_out(rows)
    policies = {
        "oracle_ceiling": (oracle_pol, policy_score(rows, oracle_pol)),
        "static_full": (static_policy(rows, "full"), policy_score(rows, static_policy(rows, "full"))),
        "static_team_no_verify": (static_policy(rows, "team_no_verify"),
                                   policy_score(rows, static_policy(rows, "team_no_verify"))),
        "static_oracle": (static_policy(rows, "oracle"),
                           policy_score(rows, static_policy(rows, "oracle"))),
        "learned_router": (learned_pol, policy_score(rows, learned_pol)),
    }

    # policy_score-by-task for CIs
    def by_task(pol):
        return [r["scores"][p] for r, p in zip(rows, pol)]

    static_full_task = by_task(static_policy(rows, "full"))
    learned_task = by_task(learned_pol)
    mean_delta, lo, hi = bootstrap_delta(learned_task, static_full_task)

    agreement_with_oracle = float(np.mean([a == b for a, b in zip(oracle_pol, learned_pol)]))

    from collections import Counter
    choice_hist = Counter(learned_pol)
    oracle_hist = Counter(oracle_pol)

    result = {
        "n_tasks": n,
        "policy_mean_scores": {k: v[1] for k, v in policies.items()},
        "learned_vs_static_full": {
            "mean_delta": mean_delta,
            "ci95": [lo, hi],
            "sig": lo > 0 or hi < 0,
        },
        "router_agreement_with_oracle_policy": agreement_with_oracle,
        "learned_router_choice_histogram": dict(choice_hist),
        "oracle_policy_choice_histogram": dict(oracle_hist),
    }

    out_json = ROOT / "shared" / "paper" / "learned_router_results.json"
    out_json.write_text(json.dumps(result, indent=2))

    lines = [
        r"\begin{table}[h]\centering\small",
        r"\caption{Task-conditional topology routing. Learned router uses logistic "
        r"regression over (category, difficulty, adversarial, multi-lang, log spec-words) "
        r"with leave-one-category-out evaluation. Scores are mean partial on "
        f"{n} tasks. $\\Delta$ vs.\\ static full in brackets is 95\\% bootstrap CI.",
        r"}",
        r"\label{tab:router}",
        r"\begin{tabular}{lc}\toprule",
        r"Policy & Mean partial \\ \midrule",
    ]
    for name, (_, score) in policies.items():
        lines.append(f"{name.replace('_', ' ')} & {score:.3f} \\\\")
    lines.append(r"\midrule")
    lines.append(
        f"Learned $-$ static full: {mean_delta:+.3f} "
        f"[{lo:+.3f}, {hi:+.3f}]{' (sig)' if result['learned_vs_static_full']['sig'] else ''}"
        r" & \\"
    )
    lines.append(r"\bottomrule\end{tabular}\end{table}")
    out_tex = ROOT / "shared" / "paper" / "table_learned_router.tex"
    out_tex.write_text("\n".join(lines))

    print(f"wrote {out_json}")
    print(f"wrote {out_tex}")
    for k, v in result["policy_mean_scores"].items():
        print(f"  {k:28s} {v:.3f}")
    print(f"  learned - static_full = {mean_delta:+.3f}  CI=[{lo:+.3f}, {hi:+.3f}]  "
          f"sig={result['learned_vs_static_full']['sig']}")
    print(f"  router agreement with oracle policy = {agreement_with_oracle:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
