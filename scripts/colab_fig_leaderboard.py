"""
Figure 3 (TeamBench): TeamBench-100 pass rate per model under the Full team
condition. Self-contained. Drop into a Colab cell. No external files needed.
"""

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path as MplPath
import numpy as np

# ─── DATA ─────────────────────────────────────────────────────────────────────
# Tuple: (model_name, pass_rate_%, n_runs_collected, family)
ROWS = [
    ("Gemini 3.1 Pro",         25.3,  99, "Google"),
    ("Claude Haiku 4.5",       23.0, 100, "Anthropic"),
    ("Gemini 3 Flash",         22.0, 100, "Google"),
    ("GPT-5.4 Mini",           22.0, 100, "OpenAI"),
    ("Claude Sonnet 4.6",      15.0, 100, "Anthropic"),
    ("Gemini 3.1 Flash Lite",  14.0, 100, "Google"),
    ("GPT-5 Nano",             10.0, 100, "OpenAI"),
]

FAMILY_COLOR = {
    "Anthropic": "#D87756",
    "Google":    "#3C90FF",
    "OpenAI":    "#F6B6CC",
}


# ─── ROUNDED-TIP HORIZONTAL BAR PATH ──────────────────────────────────────────
def add_rounded_hbars(ax, ys, vals, color, height=0.65, radius_data=2.5,
                      edge="black", linewidth=0.7):
    """Horizontal bars with flat body and rounded RIGHT corners only."""
    k = 0.5522847498
    cols = color if isinstance(color, list) else [color] * len(vals)
    for y, v, c in zip(ys, vals, cols):
        if v >= 0:
            r = min(radius_data, abs(v) / 3, height / 2)
            verts = [
                (0, y - height / 2),
                (v - r, y - height / 2),
                (v - r + k * r, y - height / 2),
                (v, y - height / 2 + r - k * r),
                (v, y - height / 2 + r),
                (v, y + height / 2 - r),
                (v, y + height / 2 - r + k * r),
                (v - r + k * r, y + height / 2),
                (v - r, y + height / 2),
                (0, y + height / 2),
                (0, y - height / 2),
            ]
        else:
            r = min(radius_data, abs(v) / 3, height / 2)
            verts = [
                (0, y - height / 2),
                (0, y + height / 2),
                (v + r, y + height / 2),
                (v + r - k * r, y + height / 2),
                (v, y + height / 2 - r + k * r),
                (v, y + height / 2 - r),
                (v, y - height / 2 + r),
                (v, y - height / 2 + r - k * r),
                (v + r - k * r, y - height / 2),
                (v + r, y - height / 2),
                (0, y - height / 2),
            ]
        codes = [
            MplPath.MOVETO, MplPath.LINETO,
            MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
            MplPath.LINETO,
            MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
            MplPath.LINETO, MplPath.CLOSEPOLY,
        ]
        ax.add_patch(mpatches.PathPatch(MplPath(verts, codes), facecolor=c,
                                        edgecolor=edge, linewidth=linewidth))


# Wilson 95% confidence interval for a binomial proportion.
def wilson(p_pct, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = p_pct / 100.0
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * np.sqrt((p * (1 - p) + z * z / (4 * n)) / n)) / denom
    return max(0.0, (center - half) * 100), min(100.0, (center + half) * 100)


# ─── PLOT ─────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "text.color": "black",
    "axes.labelcolor": "black",
    "xtick.color": "black",
    "ytick.color": "black",
    "axes.edgecolor": "black",
})

rows = sorted(ROWS, key=lambda r: r[1])  # ascending so largest is at top
labels = [r[0] for r in rows]
rates = [r[1] for r in rows]
ns = [r[2] for r in rows]
cols = [FAMILY_COLOR[r[3]] for r in rows]

err_lo, err_hi = [], []
for r, n in zip(rates, ns):
    lo, hi = wilson(r, n)
    err_lo.append(r - lo)
    err_hi.append(hi - r)

fig, ax = plt.subplots(figsize=(7.4, 3.4))
y = np.arange(len(labels))
add_rounded_hbars(ax, y, rates, color=cols, height=0.65, radius_data=2.5)
ax.errorbar(rates, y, xerr=[err_lo, err_hi], fmt="none",
            ecolor="black", elinewidth=0.7, capsize=3)
for i, (r, n) in enumerate(zip(rates, ns)):
    ax.text(r + max(err_hi[i], 0.5) + 0.4, i, f"{r:.1f}%",
            va="center", fontsize=10, color="black")
ax.set_yticks(y); ax.set_yticklabels(labels)
ax.set_xlabel("Pass rate, Full team condition (%)")
ax.set_xlim(0, 35)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v)}%"))
ax.grid(axis="x", linestyle=":", linewidth=0.5, alpha=0.5)

handles = [
    plt.Rectangle((0, 0), 1, 1, color=FAMILY_COLOR["Anthropic"],
                  ec="black", label="Anthropic"),
    plt.Rectangle((0, 0), 1, 1, color=FAMILY_COLOR["Google"],
                  ec="black", label="Google"),
    plt.Rectangle((0, 0), 1, 1, color=FAMILY_COLOR["OpenAI"],
                  ec="black", label="OpenAI"),
]
ax.legend(handles=handles, loc="lower right", fontsize=9, frameon=False)

fig.tight_layout()
plt.show()
