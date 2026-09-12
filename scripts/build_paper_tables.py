"""Build the LaTeX strings the paper needs for the cross-provider section.

Outputs to stdout:
  1. New role-marginal table cells (Planner / Executor / Verifier × {A, G, O})
     with bootstrap 95% CIs at the configuration-level resampling.
  2. Full 27-row per-config table with pass rate, partial score, total cost,
     pass/$ ratio, and average turns per run.
  3. Pareto frontier endpoints + cost extremes for the figure caption.

All numbers are computed on the dedup-by-(config, task, seed) cell store.
"""
from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path("/u/ybkim95/TeamBench/shared/role_ablation")
PER_RUN = ROOT / "results" / "per_run.jsonl"

TIER = {"A": "Haiku 4.5", "G": "Gemini-3f", "O": "GPT-5.4m"}

# Load deduped cells
cells: dict[tuple[str, str, int], dict] = {}
with PER_RUN.open() as f:
    for line in f:
        r = json.loads(line)
        if "ImportError" in (r.get("error") or ""):
            continue
        cfg = r.get("config")
        task = r.get("task_id")
        seed = r.get("seed")
        if cfg is None or task is None or seed is None:
            continue
        cells[(cfg, task, int(seed))] = r

# --------------------------------------------------------------------------
# 1. Role-marginal table with bootstrap CIs.
#    For each (role, family) cell: pool the 9 configs holding that slot
#    fixed, then bootstrap-resample at the config level (resample 9 configs
#    with replacement, recompute mean over 9*25*3 cells).
# --------------------------------------------------------------------------
def role_letters(cfg: str) -> tuple[str, str, str]:
    return cfg[1], cfg[3], cfg[5]


# config -> list of pass bools (across all tasks/seeds)
config_passes: dict[str, list[bool]] = defaultdict(list)
for (cfg, _t, _s), r in cells.items():
    config_passes[cfg].append(bool(r.get("pass")))

# role+family -> list of configs holding that slot fixed
role_configs: dict[tuple[str, str], list[str]] = defaultdict(list)
for cfg in config_passes.keys():
    p, e, v = role_letters(cfg)
    role_configs[("P", p)].append(cfg)
    role_configs[("E", e)].append(cfg)
    role_configs[("V", v)].append(cfg)


def bootstrap_ci(configs: list[str], n_iter: int = 10000, seed: int = 42) -> tuple[float, float, float]:
    rng = random.Random(seed)
    # Point estimate: mean over all runs in the held-fixed configs
    flat = [p for c in configs for p in config_passes[c]]
    point = sum(flat) / len(flat)
    # Bootstrap at config-level resampling
    means = []
    for _ in range(n_iter):
        sample = rng.choices(configs, k=len(configs))
        flat_s = [p for c in sample for p in config_passes[c]]
        means.append(sum(flat_s) / len(flat_s))
    means.sort()
    lo = means[int(0.025 * n_iter)]
    hi = means[int(0.975 * n_iter)]
    return point, lo, hi


print("=== Role-marginal table (each cell: 9 configs * 25 tasks * 3 seeds = 675 runs) ===\n")
print(f"{'Role':<10}{'Haiku':<25}{'Gemini':<25}{'GPT-5.4m':<25}")
print("-" * 85)
role_results = {}
for role, label in (("P", "Planner"), ("E", "Executor"), ("V", "Verifier")):
    cells_str = []
    role_results[role] = {}
    for letter in "AGO":
        configs = role_configs[(role, letter)]
        point, lo, hi = bootstrap_ci(configs)
        role_results[role][letter] = (point, lo, hi)
        cells_str.append(f"{point*100:5.1f}% [{lo*100:.1f}, {hi*100:.1f}]")
    print(f"{label:<10}" + "  ".join(c.ljust(23) for c in cells_str))

print("\n=== Spreads ===")
for role, label in (("P", "Planner"), ("E", "Executor"), ("V", "Verifier")):
    pts = [role_results[role][l][0] for l in "AGO"]
    spread = (max(pts) - min(pts)) * 100
    print(f"  {label}: spread = {spread:.1f}pp")

# --------------------------------------------------------------------------
# 2. Per-config full table: pass rate, partial score, total cost,
#    pass/$ ratio, avg turns. Sorted by pass rate descending.
# --------------------------------------------------------------------------
config_data: dict[str, dict] = defaultdict(lambda: {
    "passes": 0, "n": 0, "partial_sum": 0.0, "cost_sum": 0.0,
    "turns_sum": 0, "model_config": None,
})
for (cfg, _t, _s), r in cells.items():
    d = config_data[cfg]
    d["n"] += 1
    if r.get("pass"):
        d["passes"] += 1
    d["partial_sum"] += float(r.get("partial_score", 0) or 0)
    d["cost_sum"] += float(r.get("cost_usd_total", 0) or 0)
    d["turns_sum"] += int(r.get("turns_total", 0) or 0)
    if d["model_config"] is None:
        d["model_config"] = r.get("model_config") or {}

rows = []
for cfg, d in config_data.items():
    pass_rate = d["passes"] / d["n"] if d["n"] else 0
    partial = d["partial_sum"] / d["n"] if d["n"] else 0
    cost = d["cost_sum"]
    pass_per_dollar = pass_rate / cost if cost > 0 else 0
    avg_turns = d["turns_sum"] / d["n"] if d["n"] else 0
    p_letter, e_letter, v_letter = role_letters(cfg)
    rows.append({
        "cfg": cfg,
        "p_letter": p_letter,
        "e_letter": e_letter,
        "v_letter": v_letter,
        "pass_rate": pass_rate,
        "passes": d["passes"],
        "n": d["n"],
        "partial": partial,
        "cost": cost,
        "pass_per_dollar": pass_per_dollar,
        "avg_turns": avg_turns,
    })
rows.sort(key=lambda x: (-x["pass_rate"], -x["pass_per_dollar"]))

# Map letter to logo macro
LOGO = {"A": r"\logoa~Haiku-4.5", "G": r"\logog~Gemini-3f  ", "O": r"\logoo~GPT-5.4m"}

print("\n=== Full 27-row LaTeX table body ===\n")
for i, r in enumerate(rows, 1):
    bold = r["pass_rate"] == max(x["pass_rate"] for x in rows)
    bold_pp = r["pass_per_dollar"] == max(x["pass_per_dollar"] for x in rows)
    pass_str = f"\\textbf{{{r['pass_rate']*100:.1f}\\%}}" if bold else f"{r['pass_rate']*100:.1f}\\%"
    pp_str = f"\\textbf{{{r['pass_per_dollar']:.2f}}}" if bold_pp else f"{r['pass_per_dollar']:.2f}"
    print(
        f"{i:<3}& {LOGO[r['p_letter']]} & {LOGO[r['e_letter']]} & {LOGO[r['v_letter']]} & "
        f"{pass_str} & {r['partial']:.3f} & {r['cost']:.2f} & {pp_str} & {r['avg_turns']:.1f} \\\\"
    )

# --------------------------------------------------------------------------
# 3. Figure caption: pareto frontier + spreads
# --------------------------------------------------------------------------
print("\n=== For figure caption ===\n")
top = rows[0]
print(f"top pass rate: {top['cfg']} = {top['pass_rate']*100:.1f}% at ${top['cost']:.2f}")

cheapest_passing = min(
    (r for r in rows if r["pass_rate"] >= 0.20 and r["cost"] > 0),
    key=lambda r: r["cost"],
)
print(f"cheapest at ≥20% pass: {cheapest_passing['cfg']} = {cheapest_passing['pass_rate']*100:.1f}% at ${cheapest_passing['cost']:.2f}")

# Pareto frontier (along the pass-rate vs cost surface, low cost is good)
sorted_by_cost = sorted(rows, key=lambda r: r["cost"])
pareto = []
best_pass = -1
for r in sorted_by_cost:
    if r["pass_rate"] > best_pass:
        pareto.append(r)
        best_pass = r["pass_rate"]
print("\nPareto-front (cost-ascending, only configs that improve pass-rate):")
for p in pareto:
    print(f"  {p['cfg']:<8}  pass={p['pass_rate']*100:5.1f}%  cost=${p['cost']:7.2f}")

print("\n=== totals ===")
print(f"unique cells: {len(cells)}")
print(f"total cost: ${sum(d['cost_sum'] for d in config_data.values()):.2f}")
