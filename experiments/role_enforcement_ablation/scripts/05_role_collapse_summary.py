"""05_role_collapse_summary.py.

Aggregate analysis/role_compliance.jsonl into the H1 evidence table.

Reads the per-turn labels written by 04_score_compliance.py and computes
violation rates by (model, condition, declared role). H1 predicts that
violations are systematically higher under prompt_only than under enforced /
enforced_shared_history, because the same model has no OS-level constraint
keeping it in role.

Outputs:
  analysis/role_collapse_summary.json  — machine-readable aggregates
  analysis/role_collapse_summary.md    — paper-ready table

Run after 04_score_compliance.py.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

EXP_DIR = Path(__file__).resolve().parent.parent
INPUT = EXP_DIR / "analysis" / "role_compliance.jsonl"
OUT_JSON = EXP_DIR / "analysis" / "role_collapse_summary.json"
OUT_MD = EXP_DIR / "analysis" / "role_collapse_summary.md"

CONDITION_ORDER = ("prompt_only", "enforced_shared_history", "enforced")
ROLE_ORDER = ("planner", "executor", "verifier")
MODEL_ORDER = ("claude_haiku_4_5", "gemini_3_flash", "gpt_5_4_mini")


def wilson_ci(p_hat: float, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    denom = 1 + z * z / n
    centre = (p_hat + z * z / (2 * n)) / denom
    half = z * ((p_hat * (1 - p_hat) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def main() -> int:
    cells: dict[tuple[str, str, str], dict[str, int]] = defaultdict(
        lambda: {"turns": 0, "violations": 0, "vtypes": defaultdict(int)}
    )
    runs_seen: dict[tuple[str, str], set[str]] = defaultdict(set)

    with INPUT.open() as f:
        for line in f:
            r = json.loads(line)
            model = r["model"]
            cond = r["condition"]
            role = r["role_declared"]
            if cond == "unknown" or model == "pre_flight":
                continue
            key = (model, cond, role)
            cells[key]["turns"] += 1
            if r["violation"]:
                cells[key]["violations"] += 1
                cells[key]["vtypes"][r["violation_type"]] += 1
            runs_seen[(model, cond)].add(r["run_id"])

    # JSON output
    out_json: dict = {"cells": {}, "runs_per_cell": {}}
    for (model, cond, role), v in cells.items():
        rate = v["violations"] / v["turns"] if v["turns"] else 0.0
        lo, hi = wilson_ci(rate, v["turns"])
        out_json["cells"][f"{model}|{cond}|{role}"] = {
            "model": model,
            "condition": cond,
            "role": role,
            "turns": v["turns"],
            "violations": v["violations"],
            "rate": rate,
            "ci95_lo": lo,
            "ci95_hi": hi,
            "violation_types": dict(v["vtypes"]),
        }
    for (model, cond), runs in runs_seen.items():
        out_json["runs_per_cell"][f"{model}|{cond}"] = len(runs)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out_json, indent=2, default=str))

    # Markdown table
    md = ["# Role-Collapse Audit (H1 evidence)", ""]
    md.append(f"Source: {INPUT.name}; cells with condition=unknown excluded.")
    md.append("")
    md.append("Violation rate = % of turns flagged by deterministic rubric in `04_score_compliance.py`.")
    md.append("Wilson 95% CIs reported in JSON output; this table shows point estimates only.")
    md.append("")
    md.append("## Aggregate (pooled across models)")
    md.append("")
    md.append("| Condition | Role | Turns | Violations | Rate |")
    md.append("|---|---|---:|---:|---:|")
    pooled: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    for (model, cond, role), v in cells.items():
        pooled[(cond, role)][0] += v["turns"]
        pooled[(cond, role)][1] += v["violations"]
    for cond in CONDITION_ORDER:
        for role in ROLE_ORDER:
            t, viol = pooled.get((cond, role), [0, 0])
            rate = viol / t if t else 0.0
            md.append(f"| {cond} | {role} | {t} | {viol} | {rate:.1%} |")

    md.append("")
    md.append("## Per-model breakdown")
    md.append("")
    for model in MODEL_ORDER:
        md.append(f"### {model}")
        md.append("")
        md.append("| Condition | Role | Runs | Turns | Violations | Rate |")
        md.append("|---|---|---:|---:|---:|---:|")
        for cond in CONDITION_ORDER:
            for role in ROLE_ORDER:
                v = cells.get((model, cond, role))
                if not v:
                    continue
                runs = len(runs_seen.get((model, cond), set()))
                rate = v["violations"] / v["turns"] if v["turns"] else 0.0
                md.append(
                    f"| {cond} | {role} | {runs} | {v['turns']} | {v['violations']} | {rate:.1%} |"
                )
        md.append("")

    md.append("## Top violation types per condition (pooled)")
    md.append("")
    type_pool: dict[tuple[str, str], int] = defaultdict(int)
    for (_, cond, _), v in cells.items():
        for vt, c in v["vtypes"].items():
            type_pool[(cond, vt)] += c
    for cond in CONDITION_ORDER:
        types = [(vt, c) for (cc, vt), c in type_pool.items() if cc == cond]
        types.sort(key=lambda x: -x[1])
        if not types:
            continue
        md.append(f"**{cond}**:")
        for vt, c in types[:8]:
            md.append(f"- `{vt}`: {c}")
        md.append("")

    OUT_MD.write_text("\n".join(md) + "\n")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
