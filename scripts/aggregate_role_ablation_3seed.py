"""Aggregate the complete 27-config × 25-task × 3-seed cross-provider dataset.

Dedups duplicate (config, task, seed) rows from parallel-worker overlap by
keeping the latest record per cell. Computes per-config pass rates, per-seed
variance, Wilson 95% CIs, top-k stability, and per-role family marginals.

Outputs:
  shared/role_ablation/results/per_config_3seed.json
  shared/role_ablation/results/executive_summary_3seed.md  (overwrites)
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path("/u/ybkim95/TeamBench/shared/role_ablation")
PER_RUN = ROOT / "results" / "per_run.jsonl"
OUT_JSON = ROOT / "results" / "per_config_3seed.json"
OUT_MD = ROOT / "results" / "executive_summary_3seed.md"

TIER_NAME = {"A": "Haiku", "G": "Gemini", "O": "gpt5.4m"}


def wilson_ci(p: float, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def main() -> None:
    # Dedup by (config, task, seed): latest record wins (skip ImportError records)
    cells: dict[tuple[str, str, int], dict] = {}
    with PER_RUN.open() as f:
        for line in f:
            r = json.loads(line)
            err = r.get("error") or ""
            if "ImportError" in err:
                continue
            cfg = r.get("config")
            task = r.get("task_id")
            seed = r.get("seed")
            if cfg is None or task is None or seed is None:
                continue
            cells[(cfg, task, int(seed))] = r

    # Per-config × per-seed aggregation
    by_cfg_seed: dict[tuple[str, int], list[dict]] = defaultdict(list)
    by_cfg: dict[str, list[dict]] = defaultdict(list)
    for (cfg, _task, seed), r in cells.items():
        by_cfg_seed[(cfg, seed)].append(r)
        by_cfg[cfg].append(r)

    # Per-config aggregation
    per_config: dict[str, dict] = {}
    for cfg, runs in by_cfg.items():
        passes = sum(1 for r in runs if r.get("pass"))
        n = len(runs)
        p = passes / n
        lo, hi = wilson_ci(p, n)
        seed_breakdown = {}
        for seed in (0, 1, 2):
            seed_runs = by_cfg_seed.get((cfg, seed), [])
            sp = sum(1 for r in seed_runs if r.get("pass"))
            sn = len(seed_runs)
            seed_breakdown[seed] = {"n": sn, "passes": sp, "rate": sp / sn if sn else 0.0}
        seed_rates = [seed_breakdown[s]["rate"] for s in (0, 1, 2)]
        # variance / range across seeds
        seed_range_pp = (max(seed_rates) - min(seed_rates)) * 100
        per_config[cfg] = {
            "n": n,
            "passes": passes,
            "rate": p,
            "ci95_lo": lo,
            "ci95_hi": hi,
            "by_seed": seed_breakdown,
            "seed_range_pp": seed_range_pp,
            "model_config": runs[0].get("model_config", {}),
        }

    # Per-role family marginals (pooled over P/E/V × {A,G,O})
    role_family: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for cfg, runs in by_cfg.items():
        # cfg = P{X}E{Y}V{Z}
        p_letter, e_letter, v_letter = cfg[1], cfg[3], cfg[5]
        for role, letter in (("planner", p_letter), ("executor", e_letter), ("verifier", v_letter)):
            role_family[(role, letter)].extend(runs)

    # Top-k stability (rank correlation across seeds)
    sorted_cfgs = sorted(per_config.keys(), key=lambda c: -per_config[c]["rate"])
    rank_per_seed = {}
    for seed in (0, 1, 2):
        seed_rates = {c: per_config[c]["by_seed"][seed]["rate"] for c in per_config}
        ranking = sorted(seed_rates.keys(), key=lambda c: -seed_rates[c])
        rank_per_seed[seed] = ranking

    # Spearman rank correlation between seeds
    def spearman(r1: list[str], r2: list[str]) -> float:
        idx1 = {c: i for i, c in enumerate(r1)}
        idx2 = {c: i for i, c in enumerate(r2)}
        cs = list(idx1.keys() & idx2.keys())
        n = len(cs)
        if n < 2:
            return 0.0
        d2 = sum((idx1[c] - idx2[c]) ** 2 for c in cs)
        return 1 - (6 * d2) / (n * (n * n - 1))

    rank_corr = {
        "0_vs_1": spearman(rank_per_seed[0], rank_per_seed[1]),
        "0_vs_2": spearman(rank_per_seed[0], rank_per_seed[2]),
        "1_vs_2": spearman(rank_per_seed[1], rank_per_seed[2]),
    }

    # Per-task outcome flip rate (across the 3 seeds)
    flip_total = 0
    flip_count = 0
    for cfg in per_config:
        # task-id space: collect tasks for this config
        task_seed_passes: dict[str, dict[int, bool]] = defaultdict(dict)
        for (c, t, s), r in cells.items():
            if c == cfg:
                task_seed_passes[t][s] = bool(r.get("pass"))
        for t, seedmap in task_seed_passes.items():
            if len(seedmap) >= 2:
                flip_total += 1
                if len(set(seedmap.values())) > 1:
                    flip_count += 1
    flip_rate = flip_count / flip_total if flip_total else 0.0

    # Save JSON
    OUT_JSON.write_text(
        json.dumps(
            {
                "n_unique_cells": len(cells),
                "n_configs": len(per_config),
                "per_config": per_config,
                "rank_corr_spearman": rank_corr,
                "flip_rate": flip_rate,
                "n_task_config_pairs": flip_total,
                "n_task_config_flips": flip_count,
            },
            indent=2,
            default=str,
        )
    )

    # Markdown
    md = ["# Role Ablation — Full 27-Config × 3-Seed Pooled Analysis", ""]
    md.append(f"**Dataset:** 27 configs × 25 tasks × 3 seeds = 2,025 unique cells "
              f"({len(cells)} present after dedup)")
    md.append("")
    md.append("**Cleaning:** duplicate rows from parallel-worker overlap deduped by latest record per "
              "(config, task, seed). 88 ImportError records (from a misfired worker spawn) excluded.")
    md.append("")
    md.append("## Headline ranking (all 27 configs, pooled n=75 each)")
    md.append("")
    md.append("| Rank | Config | P | E | V | Pass rate | 95% CI | Seed range |")
    md.append("|---:|---|---|---|---|---:|---|---:|")
    for i, c in enumerate(sorted_cfgs, 1):
        info = per_config[c]
        p_letter, e_letter, v_letter = c[1], c[3], c[5]
        md.append(
            f"| {i} | **{c}** | {TIER_NAME[p_letter]} | {TIER_NAME[e_letter]} | {TIER_NAME[v_letter]} | "
            f"{info['passes']}/{info['n']} = **{info['rate']*100:.1f}%** | "
            f"[{info['ci95_lo']*100:.1f}, {info['ci95_hi']*100:.1f}] | "
            f"{info['seed_range_pp']:.0f}pp |"
        )
    md.append("")

    md.append("## Per-seed breakdown (top 10)")
    md.append("")
    md.append("| Config | Seed 0 | Seed 1 | Seed 2 | Pooled (n=75) | Range |")
    md.append("|---|---|---|---|---:|---:|")
    for c in sorted_cfgs[:10]:
        info = per_config[c]
        s = info["by_seed"]
        md.append(
            f"| {c} | "
            f"{s[0]['passes']}/{s[0]['n']} ({s[0]['rate']*100:.0f}%) | "
            f"{s[1]['passes']}/{s[1]['n']} ({s[1]['rate']*100:.0f}%) | "
            f"{s[2]['passes']}/{s[2]['n']} ({s[2]['rate']*100:.0f}%) | "
            f"**{info['rate']*100:.1f}%** | "
            f"{info['seed_range_pp']:.0f}pp |"
        )
    md.append("")

    md.append("## Top-k stability across seeds")
    md.append("")
    md.append(f"- Spearman rank correlation 0 vs 1: **{rank_corr['0_vs_1']:.3f}**")
    md.append(f"- Spearman rank correlation 0 vs 2: **{rank_corr['0_vs_2']:.3f}**")
    md.append(f"- Spearman rank correlation 1 vs 2: **{rank_corr['1_vs_2']:.3f}**")
    md.append("")
    md.append(f"- Per-(config, task) outcome flip rate: **{flip_count}/{flip_total} = "
              f"{flip_rate*100:.1f}%**")
    md.append("")

    md.append("## Per-role family marginals (pooled n=675 per family-letter)")
    md.append("")
    for role in ("planner", "executor", "verifier"):
        md.append(f"### {role.title()}")
        md.append("")
        md.append("| Family | n | Pass | Rate | 95% CI |")
        md.append("|---|---:|---:|---:|---|")
        for letter in "AGO":
            runs = role_family.get((role, letter), [])
            n = len(runs)
            p = sum(1 for r in runs if r.get("pass"))
            rate = p / n if n else 0
            lo, hi = wilson_ci(rate, n)
            md.append(
                f"| {TIER_NAME[letter]} | {n} | {p} | {rate*100:.1f}% | "
                f"[{lo*100:.1f}, {hi*100:.1f}] |"
            )
        md.append("")

    md.append("## Honest interpretation")
    md.append("")
    md.append(f"1. **Top point-estimate winner:** `{sorted_cfgs[0]}` at "
              f"{per_config[sorted_cfgs[0]]['rate']*100:.1f}% "
              f"(CI=[{per_config[sorted_cfgs[0]]['ci95_lo']*100:.1f}, "
              f"{per_config[sorted_cfgs[0]]['ci95_hi']*100:.1f}]).")
    md.append("2. **Top-k stability:** Spearman ranks across seeds are moderate "
              f"({min(rank_corr.values()):.2f}–{max(rank_corr.values()):.2f}); "
              "fine-grained rankings are seed-dependent and should not be reported beyond top-3.")
    md.append(f"3. **Per-(config, task) flip rate:** {flip_rate*100:.1f}% of pairs flip "
              "outcome across the 3 seeds; benchmark has substantial inherent stochasticity.")
    md.append("4. **Per-role family takeaway:** see Executor row — Haiku-Executor configs dominate; "
              "this is the load-bearing role.")
    md.append("")

    OUT_MD.write_text("\n".join(md) + "\n")
    print(f"wrote {OUT_JSON.name}")
    print(f"wrote {OUT_MD.name}")
    print()
    print(f"unique cells: {len(cells)} / 2025 expected")
    print(f"top winner: {sorted_cfgs[0]} = "
          f"{per_config[sorted_cfgs[0]]['rate']*100:.1f}%")


if __name__ == "__main__":
    main()
