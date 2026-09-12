"""Build the TeamBench-100 per-condition leaderboard table (tab:lb100-leaderboard).

Reads from the same source the figure-4 generator uses: completed .json files
plus the live .checkpoint.jsonl files for the resumed Opus run, the gpt-oss
family, and the qwen3 vLLM models that haven't graduated to a finalized .json
yet. Latest record per (model, condition) wins (highest valid-n).

Outputs a JSON snapshot (paper/v4/lb100_table_data.json) and the LaTeX cell
strings ready to drop into the table body, plus updated caption fragments
(reportable n, asterisk footnotes).
"""
from __future__ import annotations

import glob
import json
from collections import defaultdict
from pathlib import Path

REPO = Path("/u/ybkim95/TeamBench")
OUT_JSON = REPO / "paper" / "v4" / "lb100_table_data.json"

CHECKPOINT_ONLY_FILES = {
    "lb100_gpt-oss-120b_seed0":          "vllm:openai/gpt-oss-120b",
    "lb100_gpt-oss-20b_seed0":           "vllm:openai/gpt-oss-20b",
    "lb100_qwen3-30b-a3b-or_seed0":      "openrouter:qwen/qwen3-30b-a3b",
    "lb100_qwen35-0.8b_seed0":           "vllm:qwen/qwen3.5-0.8b",
    "lb100_qwen3-14b_seed0":             "vllm:qwen/qwen3-14b",
    "lb100_qwen3-8b_seed0":              "vllm:qwen/qwen3-8b",
    "lb100_qwen3-4b_seed0":              "vllm:qwen/qwen3-4b",
    "lb100_gemini25pro_oraclefull_seed0": "gemini-2.5-pro",
}

# (display label, list of model keys to coalesce, family logo macro, family)
DISPLAY = [
    ("Gemma 4 31B",            ["vllm:google/gemma-4-31B-it@http://localhost:8006/v1"], r"\logog", "Google"),
    ("GPT-5.4 Mini",           ["gpt-5.4-mini"],                                        r"\logoo", "OpenAI"),
    ("Gemini-3.1 Pro",         ["gemini-3.1-pro-preview"],                              r"\logog", "Google"),
    ("GPT-5.4",                ["gpt-5.4"],                                             r"\logoo", "OpenAI"),
    ("Claude Haiku 4.5",       ["claude-haiku-4-5-20251001"],                           r"\logoa", "Anthropic"),
    ("Gemini-3 Flash",         ["gemini-3-flash-preview"],                              r"\logog", "Google"),
    ("Claude Sonnet 4.6",      ["claude-sonnet-4-6", "openrouter:anthropic/claude-sonnet-4.6"], r"\logoa", "Anthropic"),
    ("Claude Opus 4.7",        ["openrouter:anthropic/claude-opus-4.7"],                r"\logoa", "Anthropic"),
    ("Gemini-3.1 Flash Lite",  ["gemini-3.1-flash-lite-preview"],                       r"\logog", "Google"),
    ("GPT-5 Nano",             ["gpt-5-nano"],                                          r"\logoo", "OpenAI"),
    ("GPT-5.4 Nano",           ["gpt-5.4-nano"],                                        r"\logoo", "OpenAI"),
    ("gpt-oss-20b",            ["vllm:openai/gpt-oss-20b"],                             r"\logoo", "OpenAI"),
    ("gpt-oss-120b",           ["vllm:openai/gpt-oss-120b"],                            r"\logoo", "OpenAI"),
    ("Qwen 3 32B",             ["openrouter:qwen/qwen3-32b"],                           r"\logoq", "Alibaba"),
    ("Qwen 3 14B",             ["openrouter:qwen/qwen3-14b"],                           r"\logoq", "Alibaba"),
    ("Qwen 3 8B",              ["openrouter:qwen/qwen3-8b"],                            r"\logoq", "Alibaba"),
]

# Aggregator: model_key -> condition -> [passed, valid_n]
agg: dict[str, dict[str, list[int]]] = defaultdict(
    lambda: defaultdict(lambda: [0, 0])
)


def _add(model: str, cond: str, passed: bool, error: bool):
    if error:
        return
    agg[model][cond][1] += 1
    if passed:
        agg[model][cond][0] += 1


# Pass 1: completed .json files (the canonical source)
for f in sorted(glob.glob(str(REPO / "shared/ablation_results/lb100_*.json"))):
    if any(s in f for s in ("checkpoint", "invalid", "bak", "old", "consolidated", "pre_")):
        continue
    try:
        d = json.load(open(f))
    except Exception:
        continue
    model = d.get("model") or "?"
    for r in d.get("runs", []) or []:
        cond = r.get("condition", "?")
        _add(model, cond, bool(r.get("pass")), bool(r.get("error")))

# Pass 2: checkpoint files. Take the larger snapshot per (model, cond).
for f in sorted(glob.glob(str(REPO / "shared/ablation_results/lb100_*.checkpoint.jsonl"))):
    if "invalid" in f or "bak" in f:
        continue
    stem = Path(f).name.replace(".json.checkpoint.jsonl", "")
    cond_data: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    with open(f) as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            cond = r.get("condition", "?")
            if r.get("error"):
                continue
            cond_data[cond][1] += 1
            cond_data[cond][0] += int(bool(r.get("pass", False)))

    if stem == "lb100_opus47_seed0":
        opus_key = "openrouter:anthropic/claude-opus-4.7"
        for c, (p, v) in cond_data.items():
            if v > agg[opus_key][c][1]:
                agg[opus_key][c] = [p, v]
        continue

    model = CHECKPOINT_ONLY_FILES.get(stem)
    if not model:
        continue
    if any(agg[model][c][1] > 0 for c in
           ("oracle", "restricted", "team_no_plan", "team_no_verify", "full")):
        continue
    for c, (p, v) in cond_data.items():
        agg[model][c] = [p, v]

# Build LaTeX rows
CONDITIONS = ("oracle", "restricted", "team_no_plan", "team_no_verify", "full")
COND_LABEL = {
    "oracle": "Solo", "restricted": "Restricted", "team_no_plan": "No Plan",
    "team_no_verify": "No Eval", "full": "Full",
}


def fmt(p: int, n: int) -> str:
    if n < 30:
        return r"\tba"
    return f"{p / n * 100:.1f}"


# Build display rows with sort key (Full rate desc, secondary Solo rate desc)
disp_rows = []
for label, keys, logo, fam in DISPLAY:
    # Coalesce multiple model-name aliases into one row
    merged: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for key in keys:
        for c in CONDITIONS:
            p, v = agg.get(key, {}).get(c, [0, 0])
            merged[c][0] += p
            merged[c][1] += v
    cells = dict(merged)
    full_n = cells.get("full", [0, 0])[1]
    full_rate = (cells.get("full", [0, 0])[0] / full_n * 100) if full_n >= 30 else None
    solo_p, solo_n = cells.get("oracle", [0, 0])
    solo_rate = (solo_p / solo_n * 100) if solo_n else 0.0
    disp_rows.append({
        "label": label, "keys": keys, "logo": logo, "family": fam,
        "cells": {c: cells.get(c, [0, 0]) for c in CONDITIONS},
        "full_rate": full_rate, "full_n": full_n,
        "solo_rate": solo_rate, "solo_n": solo_n,
    })

# Sort: rows with Full rate first (desc), then by Solo rate
disp_rows.sort(key=lambda r: (r["full_rate"] is None,
                               -(r["full_rate"] if r["full_rate"] is not None else r["solo_rate"])))


# Find max Full rate to bold
max_full = max((r["full_rate"] for r in disp_rows
                if r["full_rate"] is not None), default=None)

# LaTeX rows
print("=== LaTeX table body ===\n")
for r in disp_rows:
    cells_str = []
    for c in CONDITIONS:
        p, n = r["cells"][c]
        s = fmt(p, n)
        if c == "full" and s != r"\tba" and abs(float(s) - max_full) < 0.05:
            s = f"\\textbf{{{s}}}"
        cells_str.append(s)
    print(f"{r['logo']}~{r['label']:<22} & {' & '.join(cells_str.rjust(8) for cells_str in cells_str)} \\\\")

# Per-cell n footnote info
print("\n=== Per-row valid-n footnotes ===\n")
for r in disp_rows:
    parts = [f"{c}={r['cells'][c][0]}/{r['cells'][c][1]}" for c in CONDITIONS]
    print(f"  {r['label']:<25} {' '.join(parts)}")

# Save JSON snapshot
OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(
    json.dumps(
        {"computed_at": str(__import__("datetime").datetime.utcnow().isoformat()),
         "rows": disp_rows},
        indent=2, default=str,
    )
)
print(f"\nSaved snapshot to {OUT_JSON}")
