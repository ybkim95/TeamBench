#!/usr/bin/env python3
"""Generate paper figures.

Style rules:
  * Black text and axes, no blue/navy chrome.
  * Brand-accurate provider colors. Anthropic terra-cotta, Google blue, OpenAI black.
  * Pie chart palette mirrors BrowseComp: blue gradient, black labels outside.
  * Logos pre-normalized to 96 px in imgs/logos_small/.
"""

import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path as MplPath
import numpy as np
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from PIL import Image


def rounded_bar_path(x, y, w, h, radius):
    """Path with flat top and rounded top corners drawn as proper cubic
    quarter-circles. Square bottom corners. Mirrored for negative-height bars.
    """
    if h == 0:
        return MplPath([(x, y), (x + w, y)],
                       [MplPath.MOVETO, MplPath.LINETO])
    k = 0.5522847498  # cubic Bezier constant for quarter-circle
    if h > 0:
        r = min(radius, w / 3, h / 2)
        # Start bottom-left, go clockwise
        verts = [
            (x, y),                        # bottom-left
            (x + w, y),                    # bottom-right
            (x + w, y + h - r),            # right-up to arc start
            (x + w, y + h - r + k * r),    # cubic ctrl 1 (right corner)
            (x + w - r + k * r, y + h),    # cubic ctrl 2
            (x + w - r, y + h),            # top-right, flat segment start
            (x + r, y + h),                # flat top to left corner
            (x + r - k * r, y + h),        # cubic ctrl 1 (left corner)
            (x, y + h - r + k * r),        # cubic ctrl 2
            (x, y + h - r),                # left-down to base
            (x, y),                        # close
        ]
        codes = [
            MplPath.MOVETO,
            MplPath.LINETO, MplPath.LINETO,
            MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
            MplPath.LINETO,
            MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
            MplPath.CLOSEPOLY,
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
            MplPath.MOVETO,
            MplPath.LINETO, MplPath.LINETO,
            MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
            MplPath.LINETO,
            MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
            MplPath.CLOSEPOLY,
        ]
    return MplPath(verts, codes)


def add_rounded_bars(ax, xs, vals, color, width=0.78, radius_data=None,
                     edge="black", linewidth=0.7):
    """Replace matplotlib bars with rounded-top patches."""
    if radius_data is None:
        radius_data = max(abs(min(vals)), abs(max(vals))) * 0.04
    cols = color if isinstance(color, list) else [color] * len(vals)
    for x, v, c in zip(xs, vals, cols):
        path = rounded_bar_path(x - width / 2, 0, width, v, radius_data)
        ax.add_patch(mpatches.PathPatch(path, facecolor=c,
                                        edgecolor=edge, linewidth=linewidth))


def add_rounded_hbars(ax, ys, vals, color, height=0.65, radius_data=None,
                      edge="black", linewidth=0.6):
    """Horizontal bars with flat tip body and rounded RIGHT corners (positive)
    or LEFT corners (negative). Quarter-circle corners via cubic Bezier."""
    if radius_data is None:
        radius_data = max(abs(min(vals)), abs(max(vals))) * 0.04
    k = 0.5522847498
    cols = color if isinstance(color, list) else [color] * len(vals)
    for y, v, c in zip(ys, vals, cols):
        if v >= 0:
            r = min(radius_data, abs(v) / 3, height / 2)
            verts = [
                (0, y - height/2),
                (v - r, y - height/2),
                (v - r + k * r, y - height/2),
                (v, y - height/2 + r - k * r),
                (v, y - height/2 + r),
                (v, y + height/2 - r),
                (v, y + height/2 - r + k * r),
                (v - r + k * r, y + height/2),
                (v - r, y + height/2),
                (0, y + height/2),
                (0, y - height/2),
            ]
        else:
            r = min(radius_data, abs(v) / 3, height / 2)
            verts = [
                (0, y - height/2),
                (0, y + height/2),
                (v + r, y + height/2),
                (v + r - k * r, y + height/2),
                (v, y + height/2 - r + k * r),
                (v, y + height/2 - r),
                (v, y - height/2 + r),
                (v, y - height/2 + r - k * r),
                (v + r - k * r, y - height/2),
                (v + r, y - height/2),
                (0, y - height/2),
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

OUT = Path("/u/ybkim95/TeamBench/paper/v4/imgs")
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "axes.labelpad": 6,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "text.color": "black",
    "axes.labelcolor": "black",
    "xtick.color": "black",
    "ytick.color": "black",
    "axes.edgecolor": "black",
})

# Brand colors per author spec
FAMILY_COLOR = {
    "Anthropic": "#D87756",  # Anthropic clay
    "Google":    "#3C90FF",  # Gemini blue
    "OpenAI":    "#F6B6CC",  # OpenAI pastel pink
    "Alibaba":   "#7C3AED",  # Qwen purple
}

# Diverging palette for category bar charts
GBLUE  = "#4285F4"
GRED   = "#EA4335"


# -----------------------------------------------------------------------------
# Figure 1: TeamBench-100 leaderboard horizontal bar chart with CIs.
# -----------------------------------------------------------------------------

def fig_leaderboard():
    rows = [
        ("Gemini 3.1 Pro",         25.3, 99,  "Google"),
        ("Claude Haiku 4.5",       23.0, 100, "Anthropic"),
        ("Gemini 3 Flash",         22.0, 100, "Google"),
        ("GPT-5.4 Mini",           22.0, 100, "OpenAI"),
        ("Claude Sonnet 4.6",      15.0, 100, "Anthropic"),
        ("Gemini 3.1 Flash Lite",  14.0, 100, "Google"),
        ("GPT-5 Nano",             10.0, 100, "OpenAI"),
    ]
    rows = sorted(rows, key=lambda r: r[1])
    labels = [r[0] for r in rows]
    rates  = [r[1] for r in rows]
    ns     = [r[2] for r in rows]
    cols   = [FAMILY_COLOR[r[3]] for r in rows]

    def wilson(p, n, z=1.96):
        if n == 0: return 0, 0
        p = p / 100
        denom = 1 + z*z/n
        center = (p + z*z/(2*n)) / denom
        half = (z * np.sqrt((p*(1-p) + z*z/(4*n)) / n)) / denom
        return max(0, (center - half)*100), min(100, (center + half)*100)
    err_lo, err_hi = [], []
    for r, n in zip(rates, ns):
        lo, hi = wilson(r, n)
        err_lo.append(r - lo); err_hi.append(hi - r)

    fig, ax = plt.subplots(figsize=(7.4, 3.4))
    y = np.arange(len(labels))
    add_rounded_hbars(ax, y, rates, color=cols, height=0.65, radius_data=2.5)
    ax.errorbar(rates, y, xerr=[err_lo, err_hi], fmt="none",
                ecolor="black", elinewidth=0.7, capsize=3)
    for i, (r, n) in enumerate(zip(rates, ns)):
        ax.text(r + max(err_hi[i], 0.5) + 0.4, i, f"{r:.1f}%",
                va="center", fontsize=10, color="black")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Pass rate, Full team condition (%)")
    ax.set_xlim(0, 35)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v)}%"))
    ax.grid(axis="x", linestyle=":", linewidth=0.5, alpha=0.5)

    handles = [
        plt.Rectangle((0,0),1,1, color=FAMILY_COLOR["Anthropic"], ec="black", label="Anthropic"),
        plt.Rectangle((0,0),1,1, color=FAMILY_COLOR["Google"], ec="black", label="Google"),
        plt.Rectangle((0,0),1,1, color=FAMILY_COLOR["OpenAI"], ec="black", label="OpenAI"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=9, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "fig_lb100_leaderboard.pdf", bbox_inches="tight")
    plt.close(fig)


# -----------------------------------------------------------------------------
# Figure 2: Cross-provider role-mixing.
# Smaller logos, closer to x-axis. Black text. Panel (d) uses readable labels.
# -----------------------------------------------------------------------------

def _logo_img(path, zoom=0.20):
    img = Image.open(path).convert("RGBA")
    return OffsetImage(np.array(img), zoom=zoom)


def fig_role_mixing():
    # 27-configuration cross-provider grid, 25 tasks * 3 seeds = 75 runs per cell.
    # Marginal pass rates pool 9 configs * 25 tasks * 3 seeds = 675 runs per cell.
    # CI bounds are bootstrap 95% (10k iterations, configuration-level resampling).
    marginal = {
        "Planner":  {"Anthropic": 18.5, "Google": 16.4, "OpenAI": 17.5},
        "Executor": {"Anthropic": 19.4, "Google": 16.6, "OpenAI": 16.4},
        "Verifier": {"Anthropic": 17.3, "Google": 15.9, "OpenAI": 19.3},
    }
    marginal_ci = {
        "Planner":  {"Anthropic": (17.0, 20.0), "Google": (13.3, 20.0), "OpenAI": (15.3, 19.7)},
        "Executor": {"Anthropic": (17.0, 22.1), "Google": (14.4, 18.7), "OpenAI": (14.1, 18.8)},
        "Verifier": {"Anthropic": (13.9, 20.9), "Google": (14.2, 17.6), "OpenAI": (18.1, 20.4)},
    }
    # Per-config (name, pass%, cost$, planner, executor, verifier).
    # All 27 configurations at three seeds each (n=75 per cell).
    configs = [
        ("PGEAVA", 26.7, 20.52, "G", "A", "A"),
        ("POEOVA", 22.7, 10.98, "O", "O", "A"),
        ("PGEAVO", 22.7, 11.77, "G", "A", "O"),
        ("PAEAVA", 22.7, 39.58, "A", "A", "A"),
        ("POEGVG", 21.3,  3.73, "O", "G", "G"),
        ("PAEAVO", 21.3, 29.88, "A", "A", "O"),
        ("POEGVO", 20.0,  2.99, "O", "G", "O"),
        ("PAEOVO", 20.0,  9.53, "A", "O", "O"),
        ("POEOVO", 18.7,  2.09, "O", "O", "O"),
        ("PGEOVO", 18.7,  2.36, "G", "O", "O"),
        ("PAEGVO", 18.7, 12.45, "A", "G", "O"),
        ("PAEGVA", 18.7, 21.62, "A", "G", "A"),
        ("POEAVO", 17.3,  6.15, "O", "A", "O"),
        ("POEAVG", 17.3,  6.99, "O", "A", "G"),
        ("PAEGVG", 17.3, 13.34, "A", "G", "G"),
        ("PAEAVG", 17.3, 29.48, "A", "A", "G"),
        ("PGEGVO", 16.0,  3.67, "G", "G", "O"),
        ("PAEOVA", 16.0, 18.31, "A", "O", "A"),
        ("PGEOVG", 14.7,  3.33, "G", "O", "G"),
        ("PGEAVG", 14.7,  8.13, "G", "A", "G"),
        ("PAEOVG", 14.7, 10.87, "A", "O", "G"),
        ("POEAVA", 14.7, 12.41, "O", "A", "A"),
        ("PGEGVG", 13.3,  4.98, "G", "G", "G"),
        ("POEGVA", 13.3,  7.98, "O", "G", "A"),
        ("POEOVG", 12.0,  2.66, "O", "O", "G"),
        ("PGEOVA", 10.7,  7.43, "G", "O", "A"),
        ("PGEGVA", 10.7,  8.11, "G", "G", "A"),
    ]

    logo_paths = {
        "Anthropic": str(OUT / "logos_small" / "anthropic.png"),
        "Google":    str(OUT / "logos_small" / "google.png"),
        "OpenAI":    str(OUT / "logos_small" / "openai.png"),
    }
    providers = ["Anthropic", "Google", "OpenAI"]

    fig = plt.figure(figsize=(12.0, 3.6))
    gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 2.0], wspace=0.45)

    def rounded_vbar_path(x, y, w, h, rx, ry):
        """Vertical bar with flat top and small rounded TOP corners. Separate
        rx (horizontal radius, x-data units) and ry (vertical radius, y-data
        units) so the corner stays small in display coordinates regardless of
        axis aspect. Mirrors the leaderboard's rounded_hbar_path."""
        from matplotlib.path import Path as _MplPath
        k = 0.5522847498
        rx = min(rx, w / 3)
        ry = min(ry, h / 2)
        verts = [
            (x, y),                          # bottom-left
            (x + w, y),                      # bottom-right
            (x + w, y + h - ry),             # right edge up to arc
            (x + w, y + h - ry + k * ry),    # cubic ctrl
            (x + w - rx + k * rx, y + h),    # cubic ctrl
            (x + w - rx, y + h),             # top-right corner end
            (x + rx, y + h),                 # flat top
            (x + rx - k * rx, y + h),        # cubic ctrl
            (x, y + h - ry + k * ry),        # cubic ctrl
            (x, y + h - ry),                 # top-left corner end
            (x, y),                          # close
        ]
        codes = [
            _MplPath.MOVETO, _MplPath.LINETO, _MplPath.LINETO,
            _MplPath.CURVE4, _MplPath.CURVE4, _MplPath.CURVE4,
            _MplPath.LINETO,
            _MplPath.CURVE4, _MplPath.CURVE4, _MplPath.CURVE4,
            _MplPath.CLOSEPOLY,
        ]
        return _MplPath(verts, codes)

    for i, role in enumerate(["Planner", "Executor", "Verifier"]):
        ax = fig.add_subplot(gs[0, i])
        vals = [marginal[role][p] for p in providers]
        cis  = [marginal_ci[role][p] for p in providers]
        cols = [FAMILY_COLOR[p] for p in providers]
        xs = list(range(len(providers)))
        # Subtle rounded TOP corners. rx is small in x-data (about 7% of bar
        # width) and ry is larger in y-data (about 1.5% of y-axis range), which
        # cancels the axis-aspect mismatch and gives a visually small corner.
        bar_w = 0.66
        for x, v, c in zip(xs, vals, cols):
            p = rounded_vbar_path(x - bar_w / 2, 0, bar_w, v,
                                  rx=0.05, ry=0.45)
            ax.add_patch(mpatches.PathPatch(p, facecolor=c,
                                             edgecolor="black", linewidth=0.6,
                                             zorder=2))
        # Error bars (asymmetric: low/high to mean)
        yerr_low  = [v - lo for v, (lo, _hi) in zip(vals, cis)]
        yerr_high = [hi - v for v, (_lo, hi) in zip(vals, cis)]
        ax.errorbar(xs, vals, yerr=[yerr_low, yerr_high],
                    fmt="none", ecolor="black", elinewidth=0.7,
                    capsize=3, zorder=4)
        # Numeric labels above the upper CI
        for x, v, (_lo, hi) in zip(xs, vals, cis):
            ax.text(x, hi + 0.8, f"{v:.1f}%", ha="center", va="bottom",
                    fontsize=9, color="black")
        ax.set_xlim(-0.6, len(providers) - 0.4)
        ax.set_xticks(range(len(providers)))
        ax.set_xticklabels([""] * len(providers))
        for j, p in enumerate(providers):
            try:
                im = _logo_img(logo_paths[p], zoom=0.22)
                ab = AnnotationBbox(im, (j, 0), xybox=(0, -8), xycoords="data",
                                    boxcoords="offset points", frameon=False,
                                    box_alignment=(0.5, 1.0), pad=0)
                ax.add_artist(ab)
            except Exception:
                ax.set_xticklabels(["A","G","O"][:len(providers)])
        ax.set_ylim(0, 32)
        ax.set_title(f"({chr(ord('a')+i)}) {role}", fontsize=11, color="black", pad=4)
        if i == 0:
            ax.set_ylabel("Mean pass rate (%)")
        ax.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.5)

    # Panel (d): cost vs pass rate. Pareto frontier markers solid; off-frontier
    # markers transparent so the eye locks on the frontier.
    ax = fig.add_subplot(gs[0, 3])
    xs = np.array([c[2] for c in configs])
    ys = np.array([c[1] for c in configs])
    exec_to_color = {"A": FAMILY_COLOR["Anthropic"], "G": FAMILY_COLOR["Google"], "O": FAMILY_COLOR["OpenAI"]}
    cols = [exec_to_color[c[4]] for c in configs]

    # Compute Pareto frontier (cost ascending, only points that improve pass rate)
    idx = np.argsort(xs)
    pf_indices = set()
    cur_max = -1
    pf_x, pf_y = [], []
    for j in idx:
        if ys[j] > cur_max:
            pf_indices.add(int(j))
            pf_x.append(xs[j]); pf_y.append(ys[j])
            cur_max = ys[j]

    # Off-frontier markers — faded
    off_mask = [i for i in range(len(configs)) if i not in pf_indices]
    on_mask  = [i for i in range(len(configs)) if i in pf_indices]
    ax.scatter(xs[off_mask], ys[off_mask],
               c=[cols[i] for i in off_mask],
               edgecolor="black", linewidth=0.4, s=40,
               alpha=0.30, zorder=2)
    # Pareto-frontier markers — solid, slightly larger, on top
    ax.scatter(xs[on_mask], ys[on_mask],
               c=[cols[i] for i in on_mask],
               edgecolor="black", linewidth=0.8, s=80,
               alpha=1.0, zorder=4)
    # Stair-step frontier line: only horizontal/vertical segments. Each new
    # frontier point holds the previous y until its x, then jumps up to its y.
    if len(pf_x) > 0:
        step_x = [pf_x[0]]
        step_y = [pf_y[0]]
        for k in range(1, len(pf_x)):
            # horizontal at previous y to the new x
            step_x.append(pf_x[k])
            step_y.append(pf_y[k - 1])
            # vertical at the new x up to new y
            step_x.append(pf_x[k])
            step_y.append(pf_y[k])
        ax.plot(step_x, step_y, color="black", linewidth=1.2, alpha=0.85,
                zorder=3, drawstyle="default")

    # Annotate only PGEAVA (top-right anchor) and POEOVO (cheapest anchor).
    # Place labels in non-overlapping positions using axes-fraction coordinates
    # for the text and arrows back to the data points.
    label_map = {
        "PGEAVA": ("Best Heterogeneous", (0.62, 0.93)),
        "POEOVO": ("All OpenAI",         (0.05, 0.20)),
    }
    for c in configs:
        if c[0] in label_map:
            txt, (fx, fy) = label_map[c[0]]
            ax.annotate(
                txt,
                xy=(c[2], c[1]),
                xytext=(fx, fy),
                textcoords="axes fraction",
                fontsize=9, color="black", ha="left",
                arrowprops=dict(arrowstyle="-", color="black", linewidth=0.6,
                                connectionstyle="arc3,rad=0.0"),
            )
    ax.set_xscale("log")
    ax.set_xlabel("Total Cost (USD, log)")
    ax.set_ylabel("Pass rate (%)")
    ax.set_title("(d) Pareto Frontier", fontsize=11, color="black", pad=8)
    ax.set_ylim(0, 36)
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

    fig.subplots_adjust(bottom=0.30, left=0.05, right=0.98, top=0.86, wspace=0.45)
    fig.savefig(OUT / "fig_role_mixing.pdf", bbox_inches="tight")
    plt.close(fig)


# -----------------------------------------------------------------------------
# Figure 3: Per-category mean uplift. Black axes/text, two-color (blue/red) bars.
# -----------------------------------------------------------------------------

def fig_category_uplift():
    # (category, mean uplift pp, n, CI_lo, CI_hi) — bootstrap from per_task uplifts
    rows = [
        ("Testing",                 33.7, 10,  20.3,  48.6),
        ("Specification",           24.0,  3,   0.0,  45.7),
        ("Policy",                  21.4,  8,   1.5,  47.1),
        ("Operations",               7.8, 16,  -9.9,  21.0),
        ("Distributed",              2.8,  4,  -3.3,   8.8),
        ("Adversarial",              0.0,  5,   0.0,   0.0),
        ("Code Review",             -0.3,  5, -26.4,  17.4),
        ("Long-Horizon",            -0.7,  6, -31.8,  34.3),
        ("Security",                -1.6, 12, -17.2,  11.4),
        ("Data Engineering",        -1.8, 12, -18.6,  15.8),
        ("Information Retrieval",   -5.7,  8, -31.9,  12.1),
        ("Software Eng.",           -8.3, 21, -23.7,   6.8),
        ("Cross-System",           -10.0,  3, -30.0,   0.0),
        ("Multi-language",         -12.8,  6, -48.5,   7.1),
        ("Incident Response",      -16.3, 11, -37.7,   2.3),
        ("Pipeline",               -24.9,  6, -58.8,   5.8),
    ]
    rows = sorted(rows, key=lambda r: r[1])
    labels = [f"{r[0]} (n={r[2]})" for r in rows]
    vals = [r[1] for r in rows]
    err_lo = [v - r[3] for v, r in zip(vals, rows)]
    err_hi = [r[4] - v for v, r in zip(vals, rows)]
    cols = [GBLUE if v >= 0 else GRED for v in vals]

    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    y = np.arange(len(labels))
    add_rounded_hbars(ax, y, vals, color=cols, height=0.65, radius_data=6.0)
    ax.errorbar(vals, y, xerr=[err_lo, err_hi], fmt="none",
                ecolor="#444444", elinewidth=0.6, capsize=2.5)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_ylim(-0.6, len(labels) - 0.4)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.set_xlabel("Mean team uplift over Solo (points), 95% bootstrap CI")
    ax.set_xlim(-65, 55)
    ax.grid(axis="x", linestyle=":", linewidth=0.5, alpha=0.5)
    fig.tight_layout()
    fig.savefig(OUT / "fig_category_uplift.pdf", bbox_inches="tight")
    plt.close(fig)


# -----------------------------------------------------------------------------
# Figure 4: Quintile uplift. Black axes/text.
# -----------------------------------------------------------------------------

def fig_quintile_uplift():
    # Source: shared/paper/quintile_solo_stratified.json (recomputed from
    # ablation_summary.json per-task table, equal-size quintile by Solo score).
    quints = [
        ("Q1\n[0.00, 0.22]",  15.7,  5.8, 25.7),
        ("Q2\n(0.22, 0.43]",   8.8, -1.8, 19.4),
        ("Q3\n(0.43, 0.75]",  -6.8,-17.0,  3.3),
        ("Q4\n(0.75, 0.90]", -10.1,-21.7,  1.5),
        ("Q5\n(0.90, 1.00]",  -9.0,-19.4,  1.5),
    ]
    labels = [q[0] for q in quints]
    vals = [q[1] for q in quints]
    err_lo = [v - q[2] for v, q in zip(vals, quints)]
    err_hi = [q[3] - v for v, q in zip(vals, quints)]
    cols = [GBLUE if v >= 0 else GRED for v in vals]

    fig, ax = plt.subplots(figsize=(6.8, 3.4))
    x = np.arange(len(labels))
    add_rounded_bars(ax, x, vals, color=cols, width=0.7, radius_data=6.0)
    ax.errorbar(x, vals, yerr=[err_lo, err_hi], fmt="none",
                ecolor="black", elinewidth=0.7, capsize=4)
    ax.axhline(0, color="black", linewidth=0.8)
    for xi, v, lo, hi in zip(x, vals, err_lo, err_hi):
        if v >= 0:
            ax.text(xi, v + hi + 1.5, f"{v:+.1f}", ha="center", va="bottom",
                    fontsize=10, color="black")
        else:
            ax.text(xi, v - lo - 1.5, f"{v:+.1f}", ha="center", va="top",
                    fontsize=10, color="black")
    ax.set_xlim(-0.6, len(labels) - 0.4)
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_xlabel("Single-agent (Solo) score quintile (n=31 each)")
    ax.set_ylabel("Mean team uplift (points), 95% CI")
    ax.set_ylim(-30, 35)
    ax.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.5)
    fig.tight_layout()
    fig.savefig(OUT / "fig_quintile_uplift.pdf", bbox_inches="tight")
    plt.close(fig)


# -----------------------------------------------------------------------------
# Figure 5: Category mix pie. BrowseComp style:
#   * Black labels OUTSIDE in the form "Category\nNN%".
#   * Larger font.
#   * Blue gradient palette.
#   * Single Other.
# -----------------------------------------------------------------------------

def fig_category_pie():
    cats = [
        ("Other (12 categories)", 35),
        ("GitHub (broad scrape)", 17),
        ("GitHub Issues (curated)", 12),
        ("Real Data Science", 8),
        ("Incident Response", 6),
        ("Security", 6),
        ("Software Eng.", 6),
        ("Data Engineering", 5),
        ("Operations", 5),
    ]
    cats = sorted(cats, key=lambda c: -c[1])
    sizes = [c[1] for c in cats]
    total = sum(sizes)
    labels = [f"{c[0]}\n{round(100*c[1]/total)}%" for c in cats]
    # OpenAI/BrowseComp-style softer blue gradient (lighter, more breathable)
    base_blues = [
        "#1F4E96", "#3367C7", "#4F86E8", "#6FA0F0",
        "#8FB7F4", "#AFCAF7", "#C8DAF9", "#DFE7FB", "#EEF3FD",
    ]
    colors = base_blues[:len(cats)]

    fig, ax = plt.subplots(figsize=(8.6, 6.6))
    ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        labeldistance=1.12,
        startangle=90,
        counterclock=False,
        wedgeprops={"edgecolor": "#34598A", "linewidth": 1.0},
        textprops={"fontsize": 11.5, "color": "black", "ha": "center"},
    )
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(OUT / "fig_category_pie.pdf", bbox_inches="tight")
    plt.close(fig)


# -----------------------------------------------------------------------------
# Figure 6: Human-evaluation platform composite, 2x2 with EQUAL sub-figure
# heights. Each screenshot is letterboxed onto a uniform canvas.
# -----------------------------------------------------------------------------

def fig_human_eval_platform():
    files = ["interface_1.png", "iterface_2.png", "iterface_3.png", "iterface_4.png"]
    titles = ["(a) Profile and expertise", "(b) Task selection",
              "(c) Mode and role pick", "(d) Workspace and grading"]
    raw_imgs = [Image.open(OUT / f).convert("RGB") for f in files]
    # Determine target tile size (aspect: 4:3) and letterbox each image
    tile_w, tile_h = 800, 600
    composed = []
    for im in raw_imgs:
        # Fit image inside (tile_w, tile_h) preserving aspect ratio
        ratio = min(tile_w / im.width, tile_h / im.height)
        new_w = int(im.width * ratio)
        new_h = int(im.height * ratio)
        resized = im.resize((new_w, new_h), Image.LANCZOS)
        canvas = Image.new("RGB", (tile_w, tile_h), (10, 12, 25))
        x = (tile_w - new_w) // 2
        y = (tile_h - new_h) // 2
        canvas.paste(resized, (x, y))
        composed.append(canvas)

    fig, axes = plt.subplots(2, 2, figsize=(10.0, 6.0))
    for ax, img, t in zip(axes.flat, composed, titles):
        ax.imshow(img)
        ax.set_title(t, fontsize=11, color="black", pad=4)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / "fig_human_eval_platform.pdf", bbox_inches="tight", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    fig_leaderboard()
    fig_role_mixing()
    fig_category_uplift()
    fig_quintile_uplift()
    fig_category_pie()
    fig_human_eval_platform()
    print("Generated:")
    for p in sorted(OUT.glob("fig_*.pdf")):
        print(" ", p)
