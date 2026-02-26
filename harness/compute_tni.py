"""
TeamBench — Teamwork Necessity Index (TNI) computation.

Three complementary metrics:
  TNI = (S_team - S_restricted) / max(ε, S_oracle - S_restricted)
  Team Uplift = S_team - S_restricted  (always valid)
  Collaboration Efficiency = (S_team - S_restricted) / S_oracle

Supports partial scores (0.0-1.0) for granular measurement.

Usage:
    # From ablation run directories (auto-infer conditions)
    python -m harness.compute_tni --runs-dir shared/ablation_runs

    # From ablation results JSON
    python -m harness.compute_tni --ablation shared/ablation_results.json

    # From individual result files
    python -m harness.compute_tni \
        --oracle shared/oracle_results.json \
        --restricted shared/restricted_results.json \
        --team shared/team_results.json

    # Quick what-if analysis
    python -m harness.compute_tni \
        --oracle-rate 0.85 --restricted-rate 0.20 --team-rate 0.72
"""
from __future__ import annotations

import argparse
import json
import math
import os
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class TaskMetrics:
    task_id: str
    oracle_partial: float = 0.0
    restricted_partial: float = 0.0
    team_partial: float = 0.0
    no_plan_partial: float = 0.0
    no_verify_partial: float = 0.0

    @property
    def necessity_gap(self) -> float:
        return self.oracle_partial - self.restricted_partial

    @property
    def tni(self) -> float:
        gap = self.necessity_gap
        if abs(gap) < 0.05:
            return float("nan")
        raw = (self.team_partial - self.restricted_partial) / gap
        # Clamp to [-2, 2] to avoid extreme values when gap is small
        return max(-2.0, min(2.0, raw))

    @property
    def team_uplift(self) -> float:
        return self.team_partial - self.restricted_partial

    @property
    def collab_efficiency(self) -> float:
        if self.oracle_partial < 0.01:
            return 0.0
        return (self.team_partial - self.restricted_partial) / self.oracle_partial

    @property
    def planning_value(self) -> float:
        if self.no_plan_partial == 0.0 and self.team_partial == 0.0:
            return float("nan")
        return self.team_partial - self.no_plan_partial

    @property
    def verification_value(self) -> float:
        if self.no_verify_partial == 0.0 and self.team_partial == 0.0:
            return float("nan")
        return self.team_partial - self.no_verify_partial

    @property
    def classification(self) -> str:
        if self.necessity_gap > 0.1 and not math.isnan(self.tni) and self.tni > 0.2:
            return "HIGH-TNI"
        elif self.team_uplift > 0.05:
            return "TEAM-HELPS"
        elif self.team_uplift > -0.05:
            return "NEUTRAL"
        else:
            return "TEAM-HURTS"


def _infer_condition(run_path: str) -> str | None:
    """Infer ablation condition from run metadata or dialogue."""
    # Check run_meta.json first
    meta_path = os.path.join(run_path, "run_meta.json")
    if os.path.isfile(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        if "condition" in meta:
            return meta["condition"]

    # Check log directories
    logs_dir = os.path.join(run_path, "logs")
    if os.path.isdir(os.path.join(logs_dir, "oracle")):
        return "oracle"
    if os.path.isdir(os.path.join(logs_dir, "restricted")):
        return "restricted"

    # Check dialogue for planner/restricted/oracle role
    dlg_path = os.path.join(run_path, "messages", "dialogue.jsonl")
    if os.path.isfile(dlg_path):
        try:
            with open(dlg_path) as f:
                first_line = f.readline().strip()
            if first_line:
                msg = json.loads(first_line)
                role = msg.get("role", "")
                if role == "planner":
                    return "full"
                if role in ("restricted", "oracle"):
                    return role
        except (json.JSONDecodeError, KeyError):
            pass

    return None


def _get_partial_score(run_path: str) -> float | None:
    """Extract partial score from a run's score.json."""
    score_path = os.path.join(run_path, "reports", "score.json")
    if not os.path.isfile(score_path):
        return None
    with open(score_path) as f:
        score = json.load(f)
    return float(
        score.get("secondary", {}).get(
            "partial_score", 1.0 if score.get("pass") else 0.0
        )
    )


def compute_from_runs_dir(runs_dir: str) -> list[TaskMetrics]:
    """Compute per-task metrics from ablation run directories."""
    task_cond_scores: dict[str, dict[str, float]] = defaultdict(dict)

    for task_name in sorted(os.listdir(runs_dir)):
        task_path = os.path.join(runs_dir, task_name)
        if not os.path.isdir(task_path):
            continue

        for run_id in sorted(os.listdir(task_path)):
            run_path = os.path.join(task_path, run_id)
            if not os.path.isdir(run_path):
                continue

            condition = _infer_condition(run_path)
            if not condition:
                continue

            partial = _get_partial_score(run_path)
            if partial is not None:
                task_cond_scores[task_name][condition] = partial

    results = []
    for task_id, cond_scores in sorted(task_cond_scores.items()):
        m = TaskMetrics(
            task_id=task_id,
            oracle_partial=cond_scores.get("oracle", 0.0),
            restricted_partial=cond_scores.get("restricted", 0.0),
            team_partial=cond_scores.get("full", cond_scores.get("team", 0.0)),
            no_plan_partial=cond_scores.get("team_no_plan", 0.0),
            no_verify_partial=cond_scores.get("team_no_verify", 0.0),
        )
        results.append(m)

    return results


def compute_from_results_json(results_path: str | list[str]) -> list[TaskMetrics]:
    """Compute per-task metrics from one or more ablation JSON files."""
    paths = [results_path] if isinstance(results_path, str) else results_path

    task_cond_scores: dict[str, dict[str, float]] = defaultdict(dict)
    for path in paths:
        with open(path) as f:
            data = json.load(f)
        for run in data.get("runs", []):
            task_id = run["task_id"]
            condition = run["condition"]
            partial = run.get("partial_score", 1.0 if run.get("pass") else 0.0)
            task_cond_scores[task_id][condition] = float(partial)

    results = []
    for task_id, cond_scores in sorted(task_cond_scores.items()):
        m = TaskMetrics(
            task_id=task_id,
            oracle_partial=cond_scores.get("oracle", 0.0),
            restricted_partial=cond_scores.get("restricted", 0.0),
            team_partial=cond_scores.get("full", 0.0),
            no_plan_partial=cond_scores.get("team_no_plan", 0.0),
            no_verify_partial=cond_scores.get("team_no_verify", 0.0),
        )
        results.append(m)

    return results


def compute_from_individual(
    oracle_results: dict, restricted_results: dict, team_results: dict
) -> list[TaskMetrics]:
    """Compute from individual condition result files."""
    def _extract(results: dict) -> dict[str, float]:
        rates = {}
        for t in results.get("results", []):
            tid = t.get("task_id", "")
            partial = t.get("secondary", {}).get(
                "partial_score", 1.0 if t.get("pass") else 0.0
            )
            rates[tid] = float(partial)
        return rates

    oracle_rates = _extract(oracle_results)
    restricted_rates = _extract(restricted_results)
    team_rates = _extract(team_results)

    all_tasks = sorted(set(oracle_rates) | set(restricted_rates) | set(team_rates))
    results = []
    for tid in all_tasks:
        m = TaskMetrics(
            task_id=tid,
            oracle_partial=oracle_rates.get(tid, 0.0),
            restricted_partial=restricted_rates.get(tid, 0.0),
            team_partial=team_rates.get(tid, 0.0),
        )
        results.append(m)
    return results


def print_report(metrics: list[TaskMetrics]) -> None:
    """Print a formatted TNI report."""
    print("\n" + "=" * 105)
    print("TeamBench TNI Report")
    print("=" * 105)
    print(
        f"{'Task':<25} {'Oracle':>7} {'Restr':>7} {'Team':>7} "
        f"{'NecGap':>7} {'TNI':>7} {'Uplift':>7} {'CollEff':>7} "
        f"{'PlanV':>7} {'VerV':>7} {'Class':>12}"
    )
    print("-" * 105)

    valid_tni = []
    all_uplift = []

    for m in metrics:
        tni_s = f"{m.tni:.2f}" if not math.isnan(m.tni) else "N/A"
        pv = f"{m.planning_value:+.2f}" if not math.isnan(m.planning_value) else "N/A"
        vv = f"{m.verification_value:+.2f}" if not math.isnan(m.verification_value) else "N/A"

        print(
            f"{m.task_id:<25} {m.oracle_partial:>7.2f} {m.restricted_partial:>7.2f} "
            f"{m.team_partial:>7.2f} {m.necessity_gap:>+7.2f} {tni_s:>7} "
            f"{m.team_uplift:>+7.2f} {m.collab_efficiency:>7.2f} "
            f"{pv:>7} {vv:>7} {m.classification:>12}"
        )

        if not math.isnan(m.tni) and m.necessity_gap > 0.05:
            valid_tni.append(m.tni)
        all_uplift.append(m.team_uplift)

    print("-" * 105)

    avg_uplift = sum(all_uplift) / max(1, len(all_uplift))
    avg_tni = sum(valid_tni) / max(1, len(valid_tni)) if valid_tni else float("nan")

    print(f"\nAggregate Metrics ({len(metrics)} tasks):")
    print(f"  Valid TNI tasks:       {len(valid_tni)} (necessity_gap > 0.05)")
    if valid_tni:
        print(f"  Average TNI:           {avg_tni:.3f}")
    print(f"  Average Team Uplift:   {avg_uplift:+.3f}")
    helps = sum(1 for u in all_uplift if u > 0.01)
    print(f"  Tasks where team helps: {helps}/{len(all_uplift)} ({helps/max(1,len(all_uplift)):.0%})")

    # Classification summary
    classes = defaultdict(int)
    for m in metrics:
        classes[m.classification] += 1
    print(f"\n  Classification: {dict(classes)}")


def to_json(metrics: list[TaskMetrics]) -> dict:
    """Convert metrics to JSON-serializable dict."""
    tasks = []
    for m in metrics:
        tasks.append({
            "task_id": m.task_id,
            "oracle": m.oracle_partial,
            "restricted": m.restricted_partial,
            "team": m.team_partial,
            "no_plan": m.no_plan_partial,
            "no_verify": m.no_verify_partial,
            "necessity_gap": m.necessity_gap,
            "tni": m.tni if not math.isnan(m.tni) else None,
            "team_uplift": m.team_uplift,
            "collab_efficiency": m.collab_efficiency,
            "planning_value": m.planning_value if not math.isnan(m.planning_value) else None,
            "verification_value": m.verification_value if not math.isnan(m.verification_value) else None,
            "classification": m.classification,
        })

    valid_tni = [t["tni"] for t in tasks if t["tni"] is not None and t["necessity_gap"] > 0.05]
    all_uplift = [t["team_uplift"] for t in tasks]

    return {
        "tasks": tasks,
        "aggregate": {
            "count": len(tasks),
            "valid_tni_count": len(valid_tni),
            "avg_tni": sum(valid_tni) / max(1, len(valid_tni)) if valid_tni else None,
            "avg_team_uplift": sum(all_uplift) / max(1, len(all_uplift)),
            "team_helps_count": sum(1 for u in all_uplift if u > 0.01),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Compute TeamBench TNI metrics")

    ap.add_argument("--runs-dir", help="Path to ablation_runs directory")
    ap.add_argument("--ablation", nargs="+", help="Path(s) to ablation result JSON files")
    ap.add_argument("--oracle", help="Path to oracle batch results")
    ap.add_argument("--restricted", help="Path to restricted batch results")
    ap.add_argument("--team", help="Path to team batch results")
    ap.add_argument("--oracle-rate", type=float, help="Oracle rate (0-1)")
    ap.add_argument("--restricted-rate", type=float, help="Restricted rate (0-1)")
    ap.add_argument("--team-rate", type=float, help="Team rate (0-1)")
    ap.add_argument("--output", help="Write JSON results to file")
    args = ap.parse_args()

    metrics = None

    if args.runs_dir:
        metrics = compute_from_runs_dir(args.runs_dir)
    elif args.ablation:
        metrics = compute_from_results_json(args.ablation)
    elif args.oracle and args.restricted and args.team:
        oracle = json.load(open(args.oracle))
        restricted = json.load(open(args.restricted))
        team = json.load(open(args.team))
        metrics = compute_from_individual(oracle, restricted, team)
    elif args.oracle_rate is not None and args.restricted_rate is not None and args.team_rate is not None:
        m = TaskMetrics(
            task_id="manual",
            oracle_partial=args.oracle_rate,
            restricted_partial=args.restricted_rate,
            team_partial=args.team_rate,
        )
        metrics = [m]
    else:
        # Auto-detect
        if os.path.isdir("shared/ablation_runs"):
            metrics = compute_from_runs_dir("shared/ablation_runs")
        elif os.path.isfile("shared/ablation_results.json"):
            metrics = compute_from_results_json("shared/ablation_results.json")

    if not metrics:
        ap.print_help()
        print("\nNo ablation data found. Use --runs-dir, --ablation, or rate flags.")
        return

    print_report(metrics)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(to_json(metrics), f, indent=2)
        print(f"\nJSON results written to: {args.output}")


if __name__ == "__main__":
    main()
