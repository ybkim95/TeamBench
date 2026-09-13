#!/usr/bin/env python3
"""Figure 1: the scale decides whether the effect is visible.

Two panels, one x-axis (shared turn budget), and deliberately the SAME y-axis
range on both. That choice is the argument. Autoscaling each panel separately
would make the left panel look like it carries a real effect; on a common axis
it is visible that the reported scale compresses every condition into the top
fifth of the range, because 303 of 374 grader checks pass on an untouched
workspace and therefore sit in both the numerator and the denominator.

Numbers are recomputed from the sweep checkpoints at build time rather than
typed in, so the figure cannot drift away from the data behind it.

Usage:
  python scripts/make_figure1.py --model gemini3flashpreview
"""
from __future__ import annotations

import argparse
import collections
import glob
import importlib.util
import json
import os
import re
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SWEEP = os.path.join(REPO, "shared", "ablation_results", "budget_sweep", "core_tasks")


def load_curve(tag: str):
    sp = importlib.util.spec_from_file_location(
        "bc", os.path.join(REPO, "scripts", "budget_curve.py"))
    bc = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(bc)
    base = bc.load_baseline()
    out = collections.defaultdict(lambda: collections.defaultdict(dict))
    for cp in sorted(glob.glob(os.path.join(SWEEP, "*%s*.checkpoint.jsonl" % tag))):
        b = int(re.search(r"budget(\d+)_", os.path.basename(cp)).group(1))
        for line in open(cp):
            try:
                r = json.loads(line)
            except Exception:
                continue
            t, c = r.get("task_id"), r.get("condition")
            if not t or not c or t not in base:
                continue
            _adm, disc = bc.rescore(bc.checks_for(r), base[t])
            out[b][c][t] = {"raw": r.get("partial_score"), "disc": disc}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemini3flashpreview")
    ap.add_argument("--min-n", type=int, default=48,
                    help="only plot a budget whose cell is complete")
    ap.add_argument("--out", default=os.path.join(REPO, "paper", "manuscript",
                                                  "fig1_scale.pdf"))
    a = ap.parse_args()

    d = load_curve(a.model)
    budgets = sorted(b for b in d
                     if all(len(d[b].get(c) or {}) >= a.min_n
                            for c in ("oracle", "full")))
    if not budgets:
        print("no complete budget cell for %s; nothing to plot" % a.model,
              file=sys.stderr)
        return 1

    def series(cond, key):
        return [statistics.mean([v[key] for v in d[b][cond].values()
                                 if isinstance(v[key], (int, float))])
                for b in budgets]

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pubfig

    # The theme asks for Helvetica/Arial, which are absent here, and matplotlib
    # then falls back silently after emitting a findfont warning per glyph run.
    # A silent fallback means the figure in the paper is set in a different face
    # from the one the theme intends, so the substitute is named explicitly.
    import matplotlib.font_manager as fm
    have = {f.name for f in fm.fontManager.ttflist}
    for cand in ("Nimbus Sans", "Liberation Sans", "DejaVu Sans"):
        if cand in have:
            matplotlib.rcParams["font.family"] = "sans-serif"
            matplotlib.rcParams["font.sans-serif"] = [cand]
            print("font: %s" % cand)
            break

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    panels = [
        ("raw", "score as the grader reports it", axes[0]),
        ("disc", "score over discriminating checks", axes[1]),
    ]
    for key, sub, ax in panels:
        pubfig.line(
            [series("oracle", key), series("full", key)],
            x=budgets, series_names=["Solo", "Full Team"],
            x_label="shared turn budget", y_label="mean score",
            ax=ax, legend_show=(key == "raw"), marker="auto")
        ax.set_title(sub, fontsize=9)
        if ax is not axes[0]:
            # sharey already hides the ticks; the label would be a duplicate
            ax.set_ylabel("")
        # A common, full-range axis on both panels. This is the point of the
        # figure: the left panel is not flat because nothing happens, it is flat
        # because guards hold every condition near the ceiling.
        ax.set_ylim(0.0, 1.0)
        ax.set_xticks(budgets)
        ax.set_xticklabels([str(b) for b in budgets])

    # grayscale robustness: distinguish the series by dash pattern too, so the
    # figure survives being printed in black and white
    for ax in axes:
        for i, ln in enumerate(ax.get_lines()):
            ln.set_linestyle(["-", "--"][i % 2])

    # The right panel's values are small on a common axis, which is the point,
    # but the reader should still be able to read them off. Endpoint labels give
    # the exact numbers without a second table.
    span = budgets[-1] - budgets[0]
    for key, _sub, ax in panels:
        # headroom so a right-edge label is not clipped by the axes box
        ax.set_xlim(budgets[0] - 0.04 * span, budgets[-1] + 0.22 * span)
        for cond in ("oracle", "full"):
            ys = series(cond, key)
            # place the label away from the axis: below the point unless the
            # point is already near the floor, where it would land on the spine
            off = -11 if (cond == "full" and ys[-1] > 0.12) else 7
            ax.annotate("%.3f" % ys[-1], (budgets[-1], ys[-1]),
                        textcoords="offset points", xytext=(5, off),
                        fontsize=7.5, ha="left")

    # one legend for the whole figure, centred
    h, lab = axes[0].get_legend_handles_labels()
    if axes[0].get_legend():
        axes[0].get_legend().remove()
    fig.legend(h, lab, loc="upper center", ncol=2, frameon=False,
               bbox_to_anchor=(0.5, 1.06), fontsize=9)

    fig.tight_layout(rect=(0, 0, 1, 0.97))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    fig.savefig(a.out, bbox_inches="tight")
    fig.savefig(a.out.replace(".pdf", ".png"), dpi=220, bbox_inches="tight")
    print("budgets plotted: %s" % budgets)
    for key, sub, _ in panels:
        print("  %-5s Solo %s" % (key, ["%.3f" % v for v in series("oracle", key)]))
        print("  %-5s Team %s" % (key, ["%.3f" % v for v in series("full", key)]))
    print("wrote %s (and .png)" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
