"""
Figure 2 (TeamBench): Cross-provider role-mixing results on the 25-task subset.
Self-contained. Drop into a Colab cell. No external files needed.
"""

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path as MplPath
import numpy as np

# ─── DATA ─────────────────────────────────────────────────────────────────────
# Marginal pass rate of each provider in each role (averaged over 9 configs).
MARGINAL = {
    "Planner":  {"Anthropic": 23.1, "Google": 21.3, "OpenAI": 20.0},
    "Executor": {"Anthropic": 27.1, "Google": 16.9, "OpenAI": 20.4},
    "Verifier": {"Anthropic": 23.1, "Google": 18.7, "OpenAI": 22.7},
}

# Per-configuration pass rate and total cost (USD, 25 tasks).
# Tuple: (config code, pass_rate_%, cost_USD, planner, executor, verifier)
CONFIGS = [
    ("PGEAVO", 36.0, 3.64,  "G", "A", "O"),
    ("PAEAVA", 32.0, 13.07, "A", "A", "A"),
    ("PAEAVO", 32.0, 9.63,  "A", "A", "O"),
    ("PAEAVG", 28.0, 9.54,  "A", "A", "G"),
    ("PGEAVA", 28.0, 6.60,  "G", "A", "A"),
    ("PAEGVA", 24.0, 6.98,  "A", "G", "A"),
    ("PGEOVO", 24.0, 0.76,  "G", "O", "O"),
    ("POEGVG", 24.0, 1.18,  "O", "G", "G"),
    ("PGEOVA", 24.0, 3.73,  "G", "O", "A"),
    ("POEAVA", 24.0, 6.21,  "O", "A", "A"),
    ("POEOVO", 24.0, 0.65,  "O", "O", "O"),
    ("POEAVO", 24.0, 3.11,  "O", "A", "O"),
    ("POEOVA", 24.0, 3.69,  "O", "O", "A"),
    ("PAEOVA", 20.0, 6.03,  "A", "O", "A"),
    ("PAEOVG", 20.0, 3.87,  "A", "O", "G"),
    ("PAEOVO", 20.0, 2.85,  "A", "O", "O"),
    ("PGEOVG", 20.0, 1.14,  "G", "O", "G"),
    ("PGEAVG", 20.0, 3.75,  "G", "A", "G"),
    ("POEAVG", 20.0, 3.54,  "O", "A", "G"),
    ("POEGVA", 20.0, 3.99,  "O", "G", "A"),
    ("PAEGVG", 16.0, 4.43,  "A", "G", "G"),
    ("PAEGVO", 16.0, 4.18,  "A", "G", "O"),
    ("PGEGVO", 16.0, 1.22,  "G", "G", "O"),
    ("PGEGVG", 12.0, 1.46,  "G", "G", "G"),
    ("POEGVO", 12.0, 0.91,  "O", "G", "O"),
    ("PGEGVA", 12.0, 4.11,  "G", "G", "A"),
    ("POEOVG",  8.0, 0.88,  "O", "O", "G"),
]

# Brand colors per author spec.
FAMILY_COLOR = {
    "Anthropic": "#D87756",
    "Google":    "#3C90FF",
    "OpenAI":    "#F6B6CC",
}
LETTER_TO_FAMILY = {"A": "Anthropic", "G": "Google", "O": "OpenAI"}


# ─── ROUNDED-TOP BAR PATH ─────────────────────────────────────────────────────
def rounded_bar_path(x, y, w, h, radius):
    """Vertical bar with flat top and rounded TOP corners only (cubic Bezier)."""
    if h == 0:
        return MplPath([(x, y), (x + w, y)], [MplPath.MOVETO, MplPath.LINETO])
    k = 0.5522847498  # quarter-circle Bezier constant
    if h > 0:
        r = min(radius, w / 3, h / 2)
        verts = [
            (x, y),
            (x + w, y),
            (x + w, y + h - r),
            (x + w, y + h - r + k * r),
            (x + w - r + k * r, y + h),
            (x + w - r, y + h),
            (x + r, y + h),
            (x + r - k * r, y + h),
            (x, y + h - r + k * r),
            (x, y + h - r),
            (x, y),
        ]
    else:
        r = min(radius, w / 3, abs(h) / 2)
        verts = [
            (x, y),
            (x + w, y),
            (x + w, y + h + r),
            (x + w, y + h + r - k * r),
            (x + w - r + k * r, y + h),
            (x + w - r, y + h),
            (x + r, y + h),
            (x + r - k * r, y + h),
            (x, y + h + r - k * r),
            (x, y + h + r),
            (x, y),
        ]
    codes = [
        MplPath.MOVETO, MplPath.LINETO, MplPath.LINETO,
        MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
        MplPath.LINETO,
        MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
        MplPath.CLOSEPOLY,
    ]
    return MplPath(verts, codes)


def add_rounded_bars(ax, xs, vals, color, width=0.78, radius_data=6.0,
                     edge="black", linewidth=0.7):
    cols = color if isinstance(color, list) else [color] * len(vals)
    for x, v, c in zip(xs, vals, cols):
        path = rounded_bar_path(x - width / 2, 0, width, v, radius_data)
        ax.add_patch(mpatches.PathPatch(path, facecolor=c, edgecolor=edge,
                                        linewidth=linewidth))


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

fig = plt.figure(figsize=(12.0, 3.6))
gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 2.0], wspace=0.45)

providers = ["Anthropic", "Google", "OpenAI"]
short_label = {"Anthropic": "Anth.", "Google": "Goog.", "OpenAI": "OAI"}

# Panels (a)–(c): marginal effect bars per role
for i, role in enumerate(["Planner", "Executor", "Verifier"]):
    ax = fig.add_subplot(gs[0, i])
    vals = [MARGINAL[role][p] for p in providers]
    cols = [FAMILY_COLOR[p] for p in providers]
    xs = list(range(len(providers)))
    add_rounded_bars(ax, xs, vals, color=cols, width=0.78, radius_data=6.0)
    for x, v in zip(xs, vals):
        ax.text(x, v + 0.6, f"{v:.1f}%", ha="center", va="bottom",
                fontsize=9, color="black")
    ax.set_xlim(-0.6, len(providers) - 0.4)
    ax.set_xticks(range(len(providers)))
    ax.set_xticklabels([short_label[p] for p in providers])
    ax.set_ylim(0, 32)
    ax.set_title(f"({chr(ord('a') + i)}) {role}", fontsize=11, color="black", pad=4)
    if i == 0:
        ax.set_ylabel("Mean pass rate (%)")
    ax.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.5)

# Panel (d): Pareto frontier
ax = fig.add_subplot(gs[0, 3])
xs = np.array([c[2] for c in CONFIGS])
ys = np.array([c[1] for c in CONFIGS])
exec_to_color = {"A": FAMILY_COLOR["Anthropic"],
                 "G": FAMILY_COLOR["Google"],
                 "O": FAMILY_COLOR["OpenAI"]}
cols = [exec_to_color[c[4]] for c in CONFIGS]
ax.scatter(xs, ys, c=cols, edgecolor="black", linewidth=0.6, s=55, zorder=3)

# Pareto frontier
idx = np.argsort(xs)
pf_x, pf_y, cur_max = [], [], -1
for j in idx:
    if ys[j] > cur_max:
        pf_x.append(xs[j]); pf_y.append(ys[j]); cur_max = ys[j]
ax.plot(pf_x, pf_y, color="black", linewidth=1.0, alpha=0.8, zorder=2)

# Plain-language anchor annotations
for c in CONFIGS:
    if c[0] == "PGEAVO":
        ax.annotate("Best heterogeneous (Gemini→Haiku→GPT)",
                    (c[2], c[1]), xytext=(8, 6), textcoords="offset points",
                    fontsize=8, color="black", ha="left",
                    arrowprops=dict(arrowstyle="-", color="black", linewidth=0.5))
    if c[0] == "POEOVO":
        ax.annotate("All-OpenAI (cheapest)",
                    (c[2], c[1]), xytext=(12, -10), textcoords="offset points",
                    fontsize=8, color="black", ha="left",
                    arrowprops=dict(arrowstyle="-", color="black", linewidth=0.5))

ax.set_xscale("log")
ax.set_xlabel("Total spend across 25 tasks (USD, log)")
ax.set_ylabel("Pass rate (%)")
ax.set_title("(d) Pareto frontier of 27 configurations",
             fontsize=11, color="black", pad=8)
ax.set_ylim(0, 50)
ax.grid(linestyle=":", linewidth=0.5, alpha=0.5)
handles = [
    plt.Line2D([], [], marker="o", linestyle="", markerfacecolor=exec_to_color["A"],
               markeredgecolor="black", label="Exec=Anthropic"),
    plt.Line2D([], [], marker="o", linestyle="", markerfacecolor=exec_to_color["G"],
               markeredgecolor="black", label="Exec=Google"),
    plt.Line2D([], [], marker="o", linestyle="", markerfacecolor=exec_to_color["O"],
               markeredgecolor="black", label="Exec=OpenAI"),
]
ax.legend(handles=handles, fontsize=8, loc="lower right", frameon=False)

fig.subplots_adjust(bottom=0.20, left=0.05, right=0.98, top=0.86, wspace=0.45)
plt.show()
