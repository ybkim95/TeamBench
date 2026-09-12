#!/usr/bin/env python3
"""Generate paper figures for role ablation.

Produces:
  shared/role_ablation/figures/fig_pareto.pdf
  shared/role_ablation/figures/fig_role_family.pdf
  shared/role_ablation/figures/fig_cost_quality_tradeoff.pdf
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path("/u/ybkim95/TeamBench/shared/role_ablation")
FIG = ROOT / "figures"
FIG.mkdir(parents=True, exist_ok=True)

FAM = {"claude-haiku-4-5-20251001":"Haiku","gemini-3-flash-preview":"Gemini","gpt-5.4-mini":"gpt5.4m"}
COLOR = {"Haiku":"#C15A4E","Gemini":"#4E8BC1","gpt5.4m":"#6AAE5C"}

def wilson(k,n,z=1.96):
    if n==0: return (0,0)
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return max(0,c-h), min(1,c+h)

def load():
    rs=[json.loads(l) for l in open(ROOT/"results"/"per_run.jsonl")]
    # dedup + valid
    seen=set(); out=[]
    for r in rs:
        k=(r["config"],r["task_id"],r.get("seed",0))
        if k in seen: continue
        seen.add(k)
        if all((r.get("role_usage") or {}).get(ro,{}).get("model") for ro in ("planner","executor","verifier")):
            out.append(r)
    return out

def fam_of(r, role): return FAM.get(r["role_usage"][role]["model"], "?")

# ---------------------------------------------------------------------------
# Figure 1: Pareto frontier (cost vs pass rate)
# ---------------------------------------------------------------------------
def fig_pareto(clean):
    by_cfg = defaultdict(lambda: {"n":0,"pass":0,"cost":0.0})
    for r in clean:
        s=by_cfg[r["config"]]; s["n"]+=1; s["pass"]+=int(r.get("pass",False)); s["cost"]+=r.get("cost_usd_total",0)
    pts=[(c, s["cost"]/s["n"], s["pass"]/s["n"], c) for c,s in by_cfg.items()]
    pareto=set()
    for i,(n,c,p,_) in enumerate(pts):
        dom=False
        for j,(m,cc,pp,_) in enumerate(pts):
            if i==j: continue
            if cc<=c and pp>=p and (cc<c or pp>p):
                dom=True; break
        if not dom: pareto.add(n)

    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    for cfg,c,p,_ in pts:
        # color by executor family
        efam = FAM.get(next((r["role_usage"]["executor"]["model"] for r in clean if r["config"]==cfg), ""), "?")
        col = COLOR.get(efam, "gray")
        marker = "*" if cfg in pareto else "o"
        size = 220 if cfg in pareto else 80
        edge = "black" if cfg in pareto else "none"
        ax.scatter(c, p*100, c=col, s=size, marker=marker, edgecolors=edge, linewidths=1.2,
                   label=efam if efam not in [h.get_label() for h in ax.collections] else None, zorder=3)
        if cfg in pareto or p > 0.30:
            ax.annotate(cfg, (c, p*100), xytext=(6, 6), textcoords="offset points", fontsize=9, fontweight="bold")

    # draw Pareto curve
    pareto_pts = sorted([(c,p) for n,c,p,_ in pts if n in pareto])
    ax.plot([c for c,_ in pareto_pts], [p*100 for _,p in pareto_pts], "k--", alpha=0.3, zorder=2)

    ax.set_xlabel("Average cost per task (USD)", fontsize=12)
    ax.set_ylabel("Pass rate (%)", fontsize=12)
    ax.set_title("Cost–quality Pareto frontier across 27 role configs\n(colored by Executor family; stars = Pareto-optimal)", fontsize=12)
    ax.set_xscale("log")
    ax.grid(alpha=0.3)
    # Manual legend
    from matplotlib.patches import Patch
    handles = [Patch(color=COLOR["Haiku"], label="Exec: Haiku 4.5"),
               Patch(color=COLOR["Gemini"], label="Exec: Gemini-3-flash"),
               Patch(color=COLOR["gpt5.4m"], label="Exec: gpt-5.4-mini")]
    ax.legend(handles=handles, loc="lower right", fontsize=10)
    plt.tight_layout()
    out = FIG / "fig_pareto.pdf"
    plt.savefig(out); plt.savefig(FIG/"fig_pareto.png", dpi=150); plt.close()
    print(f"  wrote {out}")

# ---------------------------------------------------------------------------
# Figure 2: Per-role family pass rate with 95% CI
# ---------------------------------------------------------------------------
def fig_role_family(clean):
    by_rf = {role: defaultdict(lambda: {"n":0,"pass":0}) for role in ("planner","executor","verifier")}
    for r in clean:
        for role in ("planner","executor","verifier"):
            s=by_rf[role][fam_of(r,role)]; s["n"]+=1; s["pass"]+=int(r.get("pass",False))

    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    families = ["Haiku","Gemini","gpt5.4m"]
    for ax, role in zip(axes, ("planner","executor","verifier")):
        rates = [by_rf[role][f]["pass"]/by_rf[role][f]["n"] for f in families]
        cis = [wilson(by_rf[role][f]["pass"], by_rf[role][f]["n"]) for f in families]
        errs_lo = [r-lo for r,(lo,hi) in zip(rates, cis)]
        errs_hi = [hi-r for r,(lo,hi) in zip(rates, cis)]
        cols = [COLOR[f] for f in families]
        bars = ax.bar(families, [r*100 for r in rates], yerr=[np.array(errs_lo)*100, np.array(errs_hi)*100],
                      color=cols, capsize=6, edgecolor="black", linewidth=0.8)
        for bar, r, n, f in zip(bars, rates, [by_rf[role][f]["n"] for f in families], families):
            ax.text(bar.get_x() + bar.get_width()/2, r*100 + 2, f"{r*100:.1f}%\n(n={by_rf[role][f]['n']})",
                    ha="center", fontsize=9)
        ax.set_title(role.capitalize(), fontsize=12, fontweight="bold")
        ax.set_ylim(0, 40)
        ax.grid(axis="y", alpha=0.3)
        if role == "planner":
            ax.set_ylabel("Pass rate (%)", fontsize=11)
    fig.suptitle("Pass rate by family at each role (95% Wilson CI)", fontsize=13, y=1.02)
    plt.tight_layout()
    out = FIG / "fig_role_family.pdf"
    plt.savefig(out, bbox_inches="tight"); plt.savefig(FIG/"fig_role_family.png", dpi=150, bbox_inches="tight"); plt.close()
    print(f"  wrote {out}")

# ---------------------------------------------------------------------------
# Figure 3: Role marginal effects (bar chart)
# ---------------------------------------------------------------------------
def fig_marginal(clean):
    def marginal(target):
        other_roles = [r for r in ("planner","executor","verifier") if r != target]
        holding = defaultdict(lambda: defaultdict(lambda: {"n":0,"pass":0}))
        for r in clean:
            key = tuple(fam_of(r, ro) for ro in other_roles)
            s = holding[key][fam_of(r, target)]
            s["n"]+=1; s["pass"]+=int(r.get("pass",False))
        deltas=[]
        for key,d in holding.items():
            rates={f:s["pass"]/s["n"] for f,s in d.items() if s["n"]>=20}
            if len(rates)>=2: deltas.append(max(rates.values())-min(rates.values()))
        return deltas

    roles = ("Planner", "Executor", "Verifier")
    all_deltas = [marginal(r.lower()) for r in roles]
    means = [np.mean(d)*100 if d else 0 for d in all_deltas]
    stds = [np.std(d)*100 if d else 0 for d in all_deltas]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(roles, means, yerr=stds, color=["#888","#C15A4E","#888"], capsize=8, edgecolor="black")
    for bar, m, s in zip(bars, means, stds):
        ax.text(bar.get_x() + bar.get_width()/2, m + s + 0.5, f"+{m:.1f}pp", ha="center", fontsize=11, fontweight="bold")
    ax.set_ylabel("Avg. pass-rate spread across families (pp)", fontsize=11)
    ax.set_title("Role marginal effect: Executor choice moves pass rate most\n(avg max−min across 9 contexts)", fontsize=12)
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, max(means) * 1.5)
    plt.tight_layout()
    out = FIG / "fig_role_marginal.pdf"
    plt.savefig(out); plt.savefig(FIG/"fig_role_marginal.png", dpi=150); plt.close()
    print(f"  wrote {out}")

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    clean = load()
    print(f"Loaded {len(clean)} valid runs")
    fig_pareto(clean)
    fig_role_family(clean)
    fig_marginal(clean)
    print("Done.")
