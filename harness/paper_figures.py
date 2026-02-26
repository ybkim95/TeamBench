"""
TeamBench paper figure data generation.

Produces CSV and JSON data files suitable for plotting with matplotlib,
pgfplots, or any visualization tool.

Figures:
  - Figure 2: Per-condition partial score comparison (grouped bar chart)
  - Figure 3: Per-category team uplift (horizontal bar chart)
  - Figure 4: Planning vs Verification value scatter
  - Figure 5: Task difficulty vs team uplift

Usage:
    python -m harness.paper_figures \
        --ablation shared/ablation_5task.json shared/ablation_10task.json \
        --output-dir shared/paper/figures/
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from collections import defaultdict

from harness.paper_tables import (
    merge_ablation_files,
    runs_to_task_metrics,
    _task_category,
    CATEGORY_MAP,
)
from harness.compute_tni import TaskMetrics


def _load_task_difficulty() -> dict[str, str]:
    """Load difficulty from task.yaml files."""
    difficulties = {}
    tasks_dir = "tasks"
    if not os.path.isdir(tasks_dir):
        return difficulties
    for d in os.listdir(tasks_dir):
        yaml_path = os.path.join(tasks_dir, d, "task.yaml")
        if os.path.isfile(yaml_path):
            with open(yaml_path) as f:
                for line in f:
                    if line.strip().startswith("difficulty:"):
                        difficulties[d] = line.split(":", 1)[1].strip()
                        break
    return difficulties


def figure2_condition_comparison(
    metrics: list[TaskMetrics],
    output_dir: str,
) -> None:
    """Per-condition partial score comparison (grouped bar chart data)."""
    rows = []
    for m in sorted(metrics, key=lambda x: x.task_id):
        rows.append({
            "task_id": m.task_id,
            "category": _task_category(m.task_id),
            "oracle": round(m.oracle_partial, 3),
            "restricted": round(m.restricted_partial, 3),
            "full": round(m.team_partial, 3),
            "no_plan": round(m.no_plan_partial, 3),
            "no_verify": round(m.no_verify_partial, 3),
        })

    # Write CSV
    csv_path = os.path.join(output_dir, "fig2_conditions.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    # Write JSON (for JavaScript/pgfplots)
    json_path = os.path.join(output_dir, "fig2_conditions.json")
    with open(json_path, "w") as f:
        json.dump(rows, f, indent=2)

    print(f"  Figure 2: {csv_path}")


def figure3_category_uplift(
    metrics: list[TaskMetrics],
    output_dir: str,
) -> None:
    """Per-category team uplift (horizontal bar chart data)."""
    cat_data: dict[str, list[float]] = defaultdict(list)
    for m in metrics:
        cat = _task_category(m.task_id)
        cat_data[cat].append(m.team_uplift)

    rows = []
    for cat in sorted(cat_data, key=lambda c: sum(cat_data[c]) / len(cat_data[c])):
        uplifts = cat_data[cat]
        rows.append({
            "category": cat,
            "count": len(uplifts),
            "avg_uplift": round(sum(uplifts) / len(uplifts), 4),
            "min_uplift": round(min(uplifts), 4),
            "max_uplift": round(max(uplifts), 4),
        })

    csv_path = os.path.join(output_dir, "fig3_category_uplift.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    json_path = os.path.join(output_dir, "fig3_category_uplift.json")
    with open(json_path, "w") as f:
        json.dump(rows, f, indent=2)

    print(f"  Figure 3: {csv_path}")


def figure4_component_scatter(
    metrics: list[TaskMetrics],
    output_dir: str,
) -> None:
    """Planning Value vs Verification Value scatter plot data."""
    import math
    rows = []
    for m in metrics:
        pv = m.planning_value if not math.isnan(m.planning_value) else 0.0
        vv = m.verification_value if not math.isnan(m.verification_value) else 0.0
        rows.append({
            "task_id": m.task_id,
            "category": _task_category(m.task_id),
            "planning_value": round(pv, 4),
            "verification_value": round(vv, 4),
            "team_uplift": round(m.team_uplift, 4),
            "team_gt_oracle": m.team_partial > m.oracle_partial + 0.01,
        })

    csv_path = os.path.join(output_dir, "fig4_component_scatter.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    json_path = os.path.join(output_dir, "fig4_component_scatter.json")
    with open(json_path, "w") as f:
        json.dump(rows, f, indent=2)

    print(f"  Figure 4: {csv_path}")


def figure5_difficulty_uplift(
    metrics: list[TaskMetrics],
    output_dir: str,
) -> None:
    """Task difficulty vs team uplift data."""
    difficulties = _load_task_difficulty()
    diff_order = {"easy": 1, "medium": 2, "hard": 3, "expert": 4}

    rows = []
    for m in metrics:
        diff = difficulties.get(m.task_id, "unknown")
        rows.append({
            "task_id": m.task_id,
            "difficulty": diff,
            "difficulty_num": diff_order.get(diff, 0),
            "oracle": round(m.oracle_partial, 4),
            "full": round(m.team_partial, 4),
            "team_uplift": round(m.team_uplift, 4),
            "category": _task_category(m.task_id),
        })

    # Sort by difficulty
    rows.sort(key=lambda r: r["difficulty_num"])

    csv_path = os.path.join(output_dir, "fig5_difficulty_uplift.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    json_path = os.path.join(output_dir, "fig5_difficulty_uplift.json")
    with open(json_path, "w") as f:
        json.dump(rows, f, indent=2)

    # Also generate per-difficulty aggregation
    diff_agg: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        diff_agg[r["difficulty"]].append(r["team_uplift"])

    agg_rows = []
    for diff in ["easy", "medium", "hard", "expert"]:
        vals = diff_agg.get(diff, [])
        if vals:
            agg_rows.append({
                "difficulty": diff,
                "count": len(vals),
                "avg_uplift": round(sum(vals) / len(vals), 4),
                "avg_oracle": round(
                    sum(r["oracle"] for r in rows if r["difficulty"] == diff) / len(vals), 4
                ),
                "avg_full": round(
                    sum(r["full"] for r in rows if r["difficulty"] == diff) / len(vals), 4
                ),
            })

    agg_path = os.path.join(output_dir, "fig5_difficulty_agg.json")
    with open(agg_path, "w") as f:
        json.dump(agg_rows, f, indent=2)

    print(f"  Figure 5: {csv_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate TeamBench paper figure data")
    ap.add_argument(
        "--ablation", nargs="+", required=True,
        help="Ablation result JSON files to merge",
    )
    ap.add_argument(
        "--output-dir", default="shared/paper/figures",
        help="Directory for output files",
    )
    args = ap.parse_args()

    runs = merge_ablation_files(args.ablation)
    metrics = runs_to_task_metrics(runs)

    print(f"Generating figure data for {len(metrics)} tasks ({len(runs)} runs)")
    os.makedirs(args.output_dir, exist_ok=True)

    figure2_condition_comparison(metrics, args.output_dir)
    figure3_category_uplift(metrics, args.output_dir)
    figure4_component_scatter(metrics, args.output_dir)
    figure5_difficulty_uplift(metrics, args.output_dir)

    print(f"\nAll figure data written to: {args.output_dir}/")


if __name__ == "__main__":
    main()
