#!/usr/bin/env python3
"""Generate a clean teaser figure with the correct role names.

Three boxes (Planner, Executor, Verifier) with their access scoping listed
inside each. Arrows for plan, code, attestation. A small failure-case
annotation on the right.
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path as MplPath

OUT = Path("/u/ybkim95/TeamBench/paper/v4/imgs")

NAVY = "#0B3D91"
ORANGE = "#CC785C"
TEAL = "#10A37F"
BLUE = "#4285F4"
LIGHT_BG = "#F8F9FA"
GREY = "#6E6E6E"


def rounded_box(ax, x, y, w, h, color, edge=NAVY, lw=1.2, alpha=0.18):
    box = mpatches.FancyBboxPatch((x, y), w, h,
                                   boxstyle="round,pad=0,rounding_size=0.18",
                                   facecolor=color, alpha=alpha,
                                   edgecolor=edge, linewidth=lw)
    ax.add_patch(box)


def main():
    fig, ax = plt.subplots(figsize=(11.5, 4.0))
    ax.set_xlim(0, 14); ax.set_ylim(0, 5.6)
    ax.set_aspect("equal"); ax.axis("off")

    # ---- Task + Files panel (left)
    rounded_box(ax, 0.3, 0.4, 3.0, 4.8, GREY, alpha=0.05)
    ax.text(1.8, 4.85, "Task", ha="center", fontsize=11,
            color=NAVY, fontweight="bold")
    ax.text(1.8, 4.0,
            "Fix the UserService API\nv1 to v2 compatibility.\nPlanner specifies which\nendpoints need shims and\nwhich must NOT have them.",
            ha="center", fontsize=8, color="black")
    ax.text(1.8, 2.0, "Files", ha="center", fontsize=10,
            color=NAVY, fontweight="bold")
    ax.text(1.8, 1.35, "src/server.py\ntests/test_api.py\nREADME.md",
            ha="center", fontsize=8, color="black", family="monospace")

    # ---- Planner box (top)
    rounded_box(ax, 4.0, 3.7, 3.4, 1.6, BLUE, alpha=0.18)
    ax.text(5.7, 5.05, "Planner", ha="center", fontsize=12,
            color=BLUE, fontweight="bold")
    ax.text(5.7, 4.6, "reads spec.md (read-only)", ha="center",
            fontsize=8, color="black")
    ax.text(5.7, 4.3, "writes plan.md", ha="center",
            fontsize=8, color="black")
    ax.text(5.7, 4.0, "no code execution", ha="center",
            fontsize=8, color=GREY, style="italic")

    # ---- Executor box (bottom-left of pipeline)
    rounded_box(ax, 4.0, 0.7, 3.4, 2.2, TEAL, alpha=0.18)
    ax.text(5.7, 2.65, "Executor", ha="center", fontsize=12,
            color=TEAL, fontweight="bold")
    ax.text(5.7, 2.2, "reads brief.md only", ha="center",
            fontsize=8, color="black")
    ax.text(5.7, 1.9, "edits workspace, runs commands", ha="center",
            fontsize=8, color="black")
    ax.text(5.7, 1.6, "cannot read full spec.md", ha="center",
            fontsize=8, color=GREY, style="italic")
    ax.text(5.7, 1.1, "agent$ pytest\nFAILED test_v1_auth_should_not_exist",
            ha="center", fontsize=7.5, family="monospace", color="black")

    # ---- Verifier box (bottom-right of pipeline)
    rounded_box(ax, 8.4, 0.7, 3.4, 2.2, ORANGE, alpha=0.18)
    ax.text(10.1, 2.65, "Verifier", ha="center", fontsize=12,
            color=ORANGE, fontweight="bold")
    ax.text(10.1, 2.2, "reads spec.md + workspace (read-only)", ha="center",
            fontsize=8, color="black")
    ax.text(10.1, 1.9, "writes attestation.json (only writer)", ha="center",
            fontsize=8, color="black")
    ax.text(10.1, 1.6, "cannot edit workspace", ha="center",
            fontsize=8, color=GREY, style="italic")
    ax.text(10.1, 1.1, "verdict=fail\nshim was applied to auth (regression)",
            ha="center", fontsize=7.5, color=ORANGE)

    # ---- Verifier box (top-right) — actually the spec-validation arrow
    rounded_box(ax, 8.4, 3.7, 3.4, 1.6, ORANGE, alpha=0.10)
    ax.text(10.1, 5.05, "spec.md (read-only)", ha="center", fontsize=10,
            color=NAVY)
    ax.text(10.1, 4.6, "Verifier checks against spec", ha="center",
            fontsize=8, color="black")
    ax.text(10.1, 4.3, "Planner relays: 'DO NOT add auth shim'",
            ha="center", fontsize=8, color="black")
    ax.text(10.1, 4.0, "and the Executor still applied one",
            ha="center", fontsize=8, color=ORANGE, style="italic")

    # Arrows
    arrow_props = dict(arrowstyle="->", color=NAVY, linewidth=1.3)
    # task -> planner
    ax.annotate("", xy=(4.0, 4.5), xytext=(3.3, 3.5),
                arrowprops=arrow_props)
    # planner -> executor (plan.md)
    ax.annotate("", xy=(5.7, 2.9), xytext=(5.7, 3.7),
                arrowprops=arrow_props)
    ax.text(6.0, 3.2, "plan.md", fontsize=8, color=NAVY)
    # executor -> verifier (workspace)
    ax.annotate("", xy=(8.4, 1.8), xytext=(7.4, 1.8),
                arrowprops=arrow_props)
    ax.text(7.55, 2.0, "workspace", fontsize=7.5, color=NAVY)
    # verifier -> executor (feedback)
    ax.annotate("", xy=(7.4, 1.4), xytext=(8.4, 1.4),
                arrowprops=arrow_props)
    ax.text(7.55, 1.0, "feedback", fontsize=7.5, color=NAVY)
    # planner -> verifier (top spec note)
    ax.annotate("", xy=(8.4, 4.5), xytext=(7.4, 4.5),
                arrowprops=dict(arrowstyle="->", color=GREY, linewidth=0.8))

    # Docker icon labels
    for x in (4.0, 4.0, 8.4, 8.4):
        pass
    ax.text(4.2, 5.2, "Docker", fontsize=7, color=BLUE, fontweight="bold")
    ax.text(4.2, 2.85, "Docker", fontsize=7, color=TEAL, fontweight="bold")
    ax.text(8.6, 2.85, "Docker", fontsize=7, color=ORANGE, fontweight="bold")

    # Title-ish header
    ax.text(7.0, 5.5, "operating-system enforced role separation",
            ha="center", fontsize=10, color=NAVY, fontweight="bold")

    fig.tight_layout()
    fig.savefig(OUT / "teambench_teaser.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
    print("wrote", OUT / "teambench_teaser.pdf")
