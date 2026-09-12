#!/usr/bin/env python3
"""Final analysis: all 27 configs, comprehensive metrics and insights.

Outputs:
  shared/role_ablation/results/insights_final.md
  shared/role_ablation/results/per_config_final.json
  shared/role_ablation/latex/table_role_ablation.tex
"""
from __future__ import annotations

import itertools
import json
import math
import os
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path("/u/ybkim95/TeamBench")
ROOT = REPO / "shared" / "role_ablation"
PER_RUN = ROOT / "results" / "per_run.jsonl"
TASKS_FILE = ROOT / "tasks_25.json"
OUT_MD = ROOT / "results" / "insights_final.md"
OUT_JSON = ROOT / "results" / "per_config_final.json"
OUT_TEX = ROOT / "latex" / "table_role_ablation.tex"

FAM_OF = {
    "claude-haiku-4-5-20251001": "Haiku",
    "gemini-3-flash-preview": "Gemini",
    "gpt-5.4-mini": "gpt5.4m",
}
CODE_OF = {"Haiku": "A", "Gemini": "G", "gpt5.4m": "O"}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    c = (p + z * z / (2 * n)) / denom
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, c - h), min(1.0, c + h))


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx2 = sum((x - mx) ** 2 for x in xs)
    dy2 = sum((y - my) ** 2 for y in ys)
    if dx2 == 0 or dy2 == 0:
        return None
    return num / (dx2 ** 0.5 * dy2 ** 0.5)


def load_runs() -> list[dict]:
    rs = [json.loads(l) for l in open(PER_RUN)]
    # Dedup (keep first per (config, task, seed))
    seen = set()
    out = []
    for r in rs:
        k = (r["config"], r["task_id"], r.get("seed", 0))
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def config_info(cfg: str) -> tuple[str, str, str]:
    """Return ('Haiku','Gemini','gpt5.4m') trio for P/E/V from a config name."""
    inv = {v: k for k, v in CODE_OF.items()}
    return inv[cfg[1]], inv[cfg[3]], inv[cfg[5]]


def role_family(r: dict, role: str) -> str:
    return FAM_OF.get((r.get("role_usage") or {}).get(role, {}).get("model", ""), "?")


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def main() -> None:
    runs = load_runs()
    total = len(runs)
    n_pass = sum(1 for r in runs if r.get("pass"))
    total_cost = sum(r.get("cost_usd_total", 0.0) for r in runs)
    ngs = sum(1 for r in runs if "grader_no_score" in (r.get("failure_modes") or []))
    errs = sum(1 for r in runs if r.get("error"))

    # Per-config
    by_cfg = defaultdict(lambda: {
        "n": 0, "pass": 0, "partial_sum": 0.0, "cost": 0.0,
        "turns_sum": 0, "wall_sum": 0.0,
        "in_tokens": 0, "out_tokens": 0,
    })
    for r in runs:
        s = by_cfg[r["config"]]
        s["n"] += 1
        s["pass"] += int(r.get("pass", False))
        s["partial_sum"] += r.get("partial_score", 0.0)
        s["cost"] += r.get("cost_usd_total", 0.0)
        s["turns_sum"] += r.get("turns_total", 0)
        s["wall_sum"] += r.get("elapsed_sec", 0.0)
        for u in (r.get("role_usage") or {}).values():
            s["in_tokens"] += u.get("input_tokens", 0)
            s["out_tokens"] += u.get("output_tokens", 0)

    per_config_out = {}
    for cfg, s in by_cfg.items():
        p_fam, e_fam, v_fam = config_info(cfg)
        lo, hi = wilson(s["pass"], s["n"])
        per_config_out[cfg] = {
            "planner": p_fam, "executor": e_fam, "verifier": v_fam,
            "n": s["n"],
            "passes": s["pass"],
            "success_rate": round(s["pass"] / s["n"], 4) if s["n"] else 0,
            "ci95": [round(lo, 4), round(hi, 4)],
            "avg_partial": round(s["partial_sum"] / s["n"], 4) if s["n"] else 0,
            "total_cost_usd": round(s["cost"], 4),
            "avg_cost_per_task": round(s["cost"] / s["n"], 6) if s["n"] else 0,
            "pass_per_dollar": round(s["pass"] / s["cost"], 2) if s["cost"] > 0 else None,
            "avg_turns": round(s["turns_sum"] / s["n"], 1) if s["n"] else 0,
            "total_input_tokens": s["in_tokens"],
            "total_output_tokens": s["out_tokens"],
        }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(per_config_out, f, indent=2)

    # Role-marginals (upgrade family, hold others)
    by_role_family = {role: defaultdict(lambda: {"n": 0, "pass": 0})
                      for role in ("planner", "executor", "verifier")}
    for r in runs:
        for role in ("planner", "executor", "verifier"):
            fam = role_family(r, role)
            s = by_role_family[role][fam]
            s["n"] += 1
            s["pass"] += int(r.get("pass", False))

    # Family × role cost & behavior
    fam_role_stats = defaultdict(lambda: {"n": 0, "in": 0, "out": 0, "wall": 0.0})
    for r in runs:
        for role in ("planner", "executor", "verifier"):
            u = (r.get("role_usage") or {}).get(role, {}) or {}
            fam = FAM_OF.get(u.get("model", ""), "?")
            s = fam_role_stats[(fam, role)]
            s["n"] += 1
            s["in"] += u.get("input_tokens", 0)
            s["out"] += u.get("output_tokens", 0)
            s["wall"] += u.get("wall_sec", 0)

    # Task × config matrix (for discrimination + cross-config agreement)
    scores_by_cfg = defaultdict(dict)
    for r in runs:
        scores_by_cfg[r["config"]][r["task_id"]] = r.get("partial_score", 0.0)

    # Task discrimination
    by_task = defaultdict(list)
    for r in runs:
        by_task[r["task_id"]].append(r.get("partial_score", 0.0))
    task_rows = []
    for t, ps in by_task.items():
        m = sum(ps) / len(ps)
        std = (sum((p - m) ** 2 for p in ps) / len(ps)) ** 0.5
        task_rows.append((t, len(ps), m, std, min(ps), max(ps)))
    task_rows.sort(key=lambda x: -x[3])

    # Category breakdown
    tasks_doc = json.load(open(TASKS_FILE))
    task_cat = {t["task_id"]: t["category"] for t in tasks_doc["tasks"]}
    by_cat = defaultdict(lambda: {"n": 0, "pass": 0, "partial": 0.0})
    for r in runs:
        c = task_cat.get(r["task_id"], "?")
        s = by_cat[c]
        s["n"] += 1
        s["pass"] += int(r.get("pass", False))
        s["partial"] += r.get("partial_score", 0.0)

    # Cross-config Pearson
    configs = sorted(by_cfg.keys())
    corrs = []
    for a, b in itertools.combinations(configs, 2):
        common = set(scores_by_cfg[a]) & set(scores_by_cfg[b])
        if len(common) < 10:
            continue
        xs = [scores_by_cfg[a][t] for t in sorted(common)]
        ys = [scores_by_cfg[b][t] for t in sorted(common)]
        c = pearson(xs, ys)
        if c is not None:
            corrs.append((a, b, c, len(common)))
    corrs.sort(key=lambda x: x[2])

    # Attestation presence
    att_by_vfam = defaultdict(lambda: {"n": 0, "wrote": 0})
    pass_by_attested = {"with": {"n": 0, "p": 0}, "without": {"n": 0, "p": 0}}
    for r in runs:
        vfam = role_family(r, "verifier")
        rd = r.get("run_dir", "")
        has = bool(rd) and os.path.isfile(os.path.join(rd, "submission", "attestation.json"))
        att_by_vfam[vfam]["n"] += 1
        att_by_vfam[vfam]["wrote"] += int(has)
        key = "with" if has else "without"
        pass_by_attested[key]["n"] += 1
        pass_by_attested[key]["p"] += int(r.get("pass", False))

    # ------------------------------------------------------------------
    # Markdown report
    # ------------------------------------------------------------------
    md: list[str] = []
    md.append(f"# Role Ablation — Final Report (N={total} runs across 27 configs)\n")
    md.append(f"**Dataset:** 25 tasks (pro-rata from leaderboard-100), 1 seed.\n")
    md.append(f"**Total cost:** ${total_cost:.2f} | **Pass rate:** {n_pass}/{total} ({n_pass/total*100:.1f}%) | "
              f"**grader_no_score:** {ngs} | **errors:** {errs}\n")

    md.append("\n---\n\n## 1. All 27 configs — pass rate with 95% CI\n\n")
    md.append("| Config | P | E | V | n | Pass | Rate | 95% CI | Partial | Avg$ | Pass/$ |\n")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|\n")
    for cfg, s in sorted(per_config_out.items(), key=lambda kv: -kv[1]["success_rate"]):
        lo, hi = s["ci95"]
        ppd = s["pass_per_dollar"]
        md.append(
            f"| {cfg} | {s['planner']} | {s['executor']} | {s['verifier']} | "
            f"{s['n']} | {s['passes']} | {s['success_rate']*100:.1f}% | "
            f"[{lo*100:.0f},{hi*100:.0f}] | {s['avg_partial']:.2f} | "
            f"${s['avg_cost_per_task']:.3f} | {ppd if ppd is not None else '-'} |\n"
        )

    md.append("\n---\n\n## 2. Best family per role (pooled)\n\n")
    for role in ("planner", "executor", "verifier"):
        md.append(f"**{role.capitalize()}:**\n\n")
        md.append(f"| Family | n | Pass | Rate | 95% CI |\n|---|---|---|---|---|\n")
        fams = by_role_family[role]
        for fam in sorted(fams.keys()):
            s = fams[fam]
            lo, hi = wilson(s["pass"], s["n"])
            md.append(f"| {fam} | {s['n']} | {s['pass']} | {s['pass']/s['n']*100:.1f}% | [{lo*100:.0f},{hi*100:.0f}] |\n")
        md.append("\n")

    md.append("\n---\n\n## 3. Per-family behavioral signatures\n\n")
    md.append("| Family | Role | Avg in-tokens | Avg out-tokens | Avg wall(s) |\n")
    md.append("|---|---|---|---|---|\n")
    for (fam, role), s in sorted(fam_role_stats.items()):
        if s["n"] == 0:
            continue
        md.append(
            f"| {fam} | {role} | {s['in']//max(s['n'],1):,} | "
            f"{s['out']//max(s['n'],1):,} | {s['wall']/max(s['n'],1):.1f} |\n"
        )

    md.append("\n---\n\n## 4. Verifier attestation discipline\n\n")
    md.append("| Verifier | Attestation write rate |\n|---|---|\n")
    for fam, s in sorted(att_by_vfam.items()):
        md.append(f"| {fam} | {s['wrote']}/{s['n']} ({s['wrote']/max(s['n'],1)*100:.1f}%) |\n")

    md.append("\n**Attestation presence ⇒ pass rate:**\n\n")
    pw, pwo = pass_by_attested["with"], pass_by_attested["without"]
    md.append(f"- With attestation: {pw['p']}/{pw['n']} ({pw['p']/max(pw['n'],1)*100:.1f}%)\n")
    md.append(f"- Without attestation: {pwo['p']}/{pwo['n']} ({pwo['p']/max(pwo['n'],1)*100:.1f}%)\n")

    md.append("\n---\n\n## 5. Task discrimination\n\n")
    md.append("**Top-10 discriminating tasks (high std):**\n\n")
    md.append("| Task | n | mean | std | range |\n|---|---|---|---|---|\n")
    for t, n, m, std, lo, hi in task_rows[:10]:
        md.append(f"| {t} | {n} | {m:.2f} | {std:.2f} | [{lo:.2f}, {hi:.2f}] |\n")
    ceiling_floor = [r for r in task_rows if r[3] < 0.05]
    md.append(f"\n**Non-discriminating tasks (std<0.05):** {len(ceiling_floor)}\n\n")
    for t, n, m, std, lo, hi in ceiling_floor:
        label = "ceiling" if m > 0.8 else "floor" if m < 0.2 else "stable-partial"
        md.append(f"- {t}: mean={m:.2f} [{label}]\n")

    md.append("\n---\n\n## 6. Pass rate by task category\n\n")
    md.append("| Category | Pass | Rate | Avg partial |\n|---|---|---|---|\n")
    for c, s in sorted(by_cat.items(), key=lambda kv: -kv[1]["pass"] / max(kv[1]["n"], 1)):
        md.append(f"| {c} | {s['pass']}/{s['n']} | {s['pass']/max(s['n'],1)*100:.1f}% | {s['partial']/max(s['n'],1):.2f} |\n")

    md.append("\n---\n\n## 7. Cross-config Pearson on partial scores\n\n")
    if corrs:
        mean_r = sum(c for _, _, c, _ in corrs) / len(corrs)
        md.append(f"- **Mean pairwise r = {mean_r:.3f}**\n")
        md.append(f"\n**Lowest agreement (most disagreeing configs):**\n\n")
        for a, b, c, n in corrs[:5]:
            md.append(f"- {a} vs {b}: r={c:.2f}\n")
        md.append(f"\n**Highest agreement:**\n\n")
        for a, b, c, n in corrs[-5:]:
            md.append(f"- {a} vs {b}: r={c:.2f}\n")

    md.append("\n---\n\n## 8. Pareto frontier (cost × success)\n\n")
    points = [(cfg, s["avg_cost_per_task"], s["success_rate"]) for cfg, s in per_config_out.items()]
    pareto = []
    for p in points:
        dom = False
        for q in points:
            if q is p:
                continue
            if q[1] <= p[1] and q[2] >= p[2] and (q[1] < p[1] or q[2] > p[2]):
                dom = True
                break
        if not dom:
            pareto.append(p)
    pareto.sort(key=lambda x: x[1])
    md.append("| Config | Avg$ | Success | P-E-V |\n|---|---|---|---|\n")
    for cfg, c, s in pareto:
        p, e, v = config_info(cfg)
        md.append(f"| {cfg} | ${c:.3f} | {s*100:.1f}% | {p}-{e}-{v} |\n")

    # ------------------------------------------------------------------
    # LaTeX table (full 27 configs)
    # ------------------------------------------------------------------
    tex: list[str] = []
    tex.append("% Auto-generated by scripts/analyze_role_ablation.py")
    tex.append(r"\begin{table*}[t]")
    tex.append(r"\centering")
    tex.append(r"\small")
    tex.append(r"\caption{Heterogeneous role ablation: 27 $\{$Planner,Executor,Verifier$\}$ permutations over 3 model families "
               r"(A=Haiku 4.5, G=Gemini-3-flash, O=GPT-5.4-mini) on 25 tasks, seed=0. "
               r"95\% CI from Wilson interval.}")
    tex.append(r"\label{tab:role_ablation}")
    tex.append(r"\begin{tabular}{lccc|rrr|r}")
    tex.append(r"\toprule")
    tex.append(r"Config & Planner & Executor & Verifier & Pass & CI$_{95}$ & Avg cost & Pass/\$ \\")
    tex.append(r"\midrule")
    for cfg, s in sorted(per_config_out.items(), key=lambda kv: -kv[1]["success_rate"]):
        lo, hi = s["ci95"]
        ppd = f"{s['pass_per_dollar']:.1f}" if s["pass_per_dollar"] is not None else "--"
        tex.append(
            f"{cfg} & {s['planner']} & {s['executor']} & {s['verifier']} "
            f"& {s['success_rate']*100:.1f}\\% & [{lo*100:.0f},{hi*100:.0f}] & "
            f"\\${s['avg_cost_per_task']:.3f} & {ppd} \\\\"
        )
    tex.append(r"\bottomrule")
    tex.append(r"\end{tabular}")
    tex.append(r"\end{table*}")

    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_TEX, "w") as f:
        f.write("\n".join(tex) + "\n")

    with open(OUT_MD, "w") as f:
        f.writelines(md)

    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_TEX}")
    print(f"\nSummary: {total} runs, {n_pass} passes ({n_pass/total*100:.1f}%), ${total_cost:.2f}")


if __name__ == "__main__":
    main()
