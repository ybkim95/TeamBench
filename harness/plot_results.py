"""
TeamBench paper figure generation using matplotlib.

Produces publication-ready PDF/PNG figures from ablation data.

Usage:
    python -m harness.plot_results \
        --ablation shared/ablation_5task.json shared/ablation_10task.json \
        --output-dir shared/paper/figures/
"""
from __future__ import annotations

import argparse
import json
import math
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from harness.paper_tables import (
    merge_ablation_files,
    runs_to_task_metrics,
    _task_category,
)
from harness.compute_tni import TaskMetrics


# Paper-quality defaults
plt.rcParams.update({
    "font.size": 10,
    "font.family": "serif",
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.1,
})

CONDITION_COLORS = {
    "oracle": "#2196F3",
    "restricted": "#FF9800",
    "full": "#4CAF50",
    "no_plan": "#9C27B0",
    "no_verify": "#F44336",
}

CONDITION_LABELS = {
    "oracle": "Oracle",
    "restricted": "Restricted",
    "full": "Full Team",
    "no_plan": "No Planner",
    "no_verify": "No Verifier",
}


def plot_condition_comparison(
    metrics: list[TaskMetrics],
    output_dir: str,
) -> None:
    """Figure 2: Grouped bar chart of per-condition partial scores."""
    tasks = sorted(metrics, key=lambda m: -m.team_partial)
    n = len(tasks)
    x = np.arange(n)
    width = 0.15

    fig, ax = plt.subplots(figsize=(max(8, n * 0.8), 4.5))

    conditions = [
        ("oracle", [m.oracle_partial for m in tasks]),
        ("restricted", [m.restricted_partial for m in tasks]),
        ("full", [m.team_partial for m in tasks]),
        ("no_plan", [m.no_plan_partial for m in tasks]),
        ("no_verify", [m.no_verify_partial for m in tasks]),
    ]

    for i, (cond, vals) in enumerate(conditions):
        offset = (i - 2) * width
        bars = ax.bar(
            x + offset, vals, width,
            label=CONDITION_LABELS[cond],
            color=CONDITION_COLORS[cond],
            alpha=0.85,
            edgecolor="white",
            linewidth=0.5,
        )

    ax.set_xlabel("Task")
    ax.set_ylabel("Partial Score")
    ax.set_title("Per-Task Ablation: Partial Scores by Condition")
    ax.set_xticks(x)
    ax.set_xticklabels(
        [m.task_id.replace("_", "\n", 1) for m in tasks],
        rotation=45, ha="right", fontsize=7,
    )
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper right", ncol=2, framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    path = os.path.join(output_dir, "fig2_conditions.pdf")
    fig.savefig(path)
    plt.close(fig)
    print(f"  {path}")


def plot_category_uplift(
    metrics: list[TaskMetrics],
    output_dir: str,
) -> None:
    """Figure 3: Horizontal bar chart of per-category team uplift."""
    cat_data: dict[str, list[float]] = defaultdict(list)
    for m in metrics:
        cat = _task_category(m.task_id)
        cat_data[cat].append(m.team_uplift)

    cats = sorted(cat_data, key=lambda c: sum(cat_data[c]) / len(cat_data[c]))
    avgs = [sum(cat_data[c]) / len(cat_data[c]) for c in cats]
    colors = ["#4CAF50" if v > 0 else "#F44336" for v in avgs]

    fig, ax = plt.subplots(figsize=(7, max(3, len(cats) * 0.5)))
    y = np.arange(len(cats))
    bars = ax.barh(y, avgs, color=colors, alpha=0.85, edgecolor="white", height=0.6)

    # Add value labels
    for bar, val in zip(bars, avgs):
        x_pos = bar.get_width()
        ha = "left" if val >= 0 else "right"
        ax.text(x_pos + 0.01 * (1 if val >= 0 else -1), bar.get_y() + bar.get_height() / 2,
                f"{val:+.2f}", va="center", ha=ha, fontsize=8)

    ax.set_yticks(y)
    ax.set_yticklabels([f"{c} (n={len(cat_data[c])})" for c in cats])
    ax.set_xlabel("Team Uplift (Full - Restricted)")
    ax.set_title("Team Uplift by Category")
    ax.axvline(x=0, color="black", linewidth=0.8)
    ax.grid(axis="x", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    path = os.path.join(output_dir, "fig3_category_uplift.pdf")
    fig.savefig(path)
    plt.close(fig)
    print(f"  {path}")


def plot_component_scatter(
    metrics: list[TaskMetrics],
    output_dir: str,
) -> None:
    """Figure 4: Planning Value vs Verification Value scatter."""
    fig, ax = plt.subplots(figsize=(6, 5))

    for m in metrics:
        pv = m.planning_value if not math.isnan(m.planning_value) else 0.0
        vv = m.verification_value if not math.isnan(m.verification_value) else 0.0
        color = "#4CAF50" if m.team_partial > m.oracle_partial + 0.01 else "#2196F3"
        marker = "^" if m.team_partial > m.oracle_partial + 0.01 else "o"
        ax.scatter(pv, vv, c=color, marker=marker, s=80, alpha=0.8, edgecolors="white", linewidth=0.5)
        ax.annotate(
            m.task_id.split("_")[0],
            (pv, vv), fontsize=6,
            xytext=(4, 4), textcoords="offset points",
        )

    ax.set_xlabel("Planning Value (Full - No Planner)")
    ax.set_ylabel("Verification Value (Full - No Verifier)")
    ax.set_title("Component Contribution Analysis")
    ax.axhline(y=0, color="gray", linewidth=0.5, linestyle="--")
    ax.axvline(x=0, color="gray", linewidth=0.5, linestyle="--")
    ax.grid(alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Legend
    team_wins = mpatches.Patch(color="#4CAF50", label="Team > Oracle")
    oracle_wins = mpatches.Patch(color="#2196F3", label="Oracle >= Team")
    ax.legend(handles=[team_wins, oracle_wins], loc="upper right")

    path = os.path.join(output_dir, "fig4_components.pdf")
    fig.savefig(path)
    plt.close(fig)
    print(f"  {path}")


def plot_oracle_vs_team(
    metrics: list[TaskMetrics],
    output_dir: str,
) -> None:
    """Figure 5: Oracle vs Full Team scatter with y=x reference line."""
    fig, ax = plt.subplots(figsize=(5.5, 5))

    for m in metrics:
        color = "#4CAF50" if m.team_partial > m.oracle_partial + 0.01 else "#F44336"
        ax.scatter(m.oracle_partial, m.team_partial, c=color, s=80, alpha=0.8,
                   edgecolors="white", linewidth=0.5)
        ax.annotate(
            m.task_id.split("_")[0],
            (m.oracle_partial, m.team_partial), fontsize=6,
            xytext=(4, 4), textcoords="offset points",
        )

    # y=x reference line
    ax.plot([0, 1], [0, 1], "k--", alpha=0.3, linewidth=1)
    ax.fill_between([0, 1], [0, 1], [1, 1], alpha=0.05, color="green")
    ax.fill_between([0, 1], [0, 0], [0, 1], alpha=0.05, color="red")

    ax.set_xlabel("Oracle Partial Score")
    ax.set_ylabel("Full Team Partial Score")
    ax.set_title("Oracle vs. Full Team Performance")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.text(0.15, 0.85, "Team wins", fontsize=9, color="#4CAF50", alpha=0.6, transform=ax.transAxes)
    ax.text(0.65, 0.15, "Oracle wins", fontsize=9, color="#F44336", alpha=0.6, transform=ax.transAxes)

    path = os.path.join(output_dir, "fig5_oracle_vs_team.pdf")
    fig.savefig(path)
    plt.close(fig)
    print(f"  {path}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate TeamBench paper figures")
    ap.add_argument("--ablation", nargs="+", required=True, help="Ablation JSON files")
    ap.add_argument("--output-dir", default="shared/paper/figures", help="Output directory")
    ap.add_argument("--format", default="pdf", choices=["pdf", "png"], help="Output format")
    args = ap.parse_args()

    runs = merge_ablation_files(args.ablation)
    metrics = runs_to_task_metrics(runs)

    print(f"Generating figures for {len(metrics)} tasks ({len(runs)} runs)")
    os.makedirs(args.output_dir, exist_ok=True)

    plot_condition_comparison(metrics, args.output_dir)
    plot_category_uplift(metrics, args.output_dir)
    plot_component_scatter(metrics, args.output_dir)
    plot_oracle_vs_team(metrics, args.output_dir)

    print(f"\nAll figures saved to: {args.output_dir}/")


if __name__ == "__main__":
    main()
