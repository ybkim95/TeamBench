"""Compute mean partial score (alongside binary pass rate) per (model, cond)
on TeamBench-100, with the same task-level dedup as aggregate_lb100_proper.py.
Writes shared/paper/lb100_partial_aggregate.json and prints LaTeX rows for
tab:partial-scores.
"""
from __future__ import annotations

import glob
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path("/u/ybkim95/TeamBench")
RES = ROOT / "shared" / "ablation_results"
OUT = ROOT / "shared" / "paper" / "lb100_partial_aggregate.json"

CONDITIONS = ("oracle", "restricted", "team_no_plan", "team_no_verify", "full")

COALESCE = {
    "claude-sonnet-4-6": "claude-sonnet-4-6",
    "openrouter:anthropic/claude-sonnet-4.6": "claude-sonnet-4-6",
    "openrouter:anthropic/claude-opus-4.7": "claude-opus-4-7",
    "claude-haiku-4-5-20251001": "claude-haiku-4-5",
    "openrouter:anthropic/claude-haiku-4.5": "claude-haiku-4-5",
    "gemini-3-flash-preview": "gemini-3-flash-preview",
    "gemini-3.1-pro-preview": "gemini-3-1-pro-preview",
    "gemini-3.1-flash-lite-preview": "gemini-3-1-flash-lite-preview",
    "gpt-5.4": "gpt-5-4",
    "gpt-5.4-mini": "gpt-5-4-mini",
    "gpt-5.4-nano": "gpt-5-4-nano",
    "gpt-5-nano": "gpt-5-nano",
    "openrouter:qwen/qwen3-32b": "qwen3-32b",
    "openrouter:qwen/qwen3-14b": "qwen3-14b",
    "openrouter:qwen/qwen3-8b": "qwen3-8b",
    "openrouter:qwen/qwen3-30b-a3b": "qwen3-30b-a3b",
    "openrouter:openai/gpt-oss-120b": "gpt-oss-120b",
    "openrouter:openai/gpt-oss-20b": "gpt-oss-20b",
    "vllm:openai/gpt-oss-120b": "gpt-oss-120b",
    "vllm:openai/gpt-oss-20b": "gpt-oss-20b",
    "vllm:google/gemma-4-31B-it@http://localhost:8006/v1": "gemma-4-31b",
    "vllm:qwen/qwen3.5-0.8b": "qwen3.5-0.8b",
    "vllm:qwen/qwen3-14b": "qwen3-14b",
    "vllm:qwen/qwen3-8b": "qwen3-8b",
    "vllm:qwen/qwen3-4b": "qwen3-4b",
    "gemini-2.5-pro": "gemini-2-5-pro",
}
CHECKPOINT_STEM_TO_MODEL = {
    "lb100_haiku45_3cond_seed0":          "claude-haiku-4-5",
    "lb100_haiku45_oraclefull_seed0":     "claude-haiku-4-5",
    "lb100_haiku45_full_resume":          "claude-haiku-4-5",
    "lb100_sonnet46_3cond_seed0":         "claude-sonnet-4-6",
    "lb100_sonnet46_oraclefull_seed0":    "claude-sonnet-4-6",
    "lb100_sonnet46_full_resume":         "claude-sonnet-4-6",
    "lb100_sonnet46_full_resume2":        "claude-sonnet-4-6",
    "lb100_sonnet46_full_resume3":        "claude-sonnet-4-6",
    "lb100_opus47_seed0":                 "claude-opus-4-7",
    "lb100_gpt54_3cond_seed0":            "gpt-5-4",
    "lb100_gpt54_oraclefull_seed0":       "gpt-5-4",
    "lb100_gpt5mini_5cond_seed0":         "gpt-5-4-mini",
    "lb100_gpt-5.4-mini_oraclefull_seed0": "gpt-5-4-mini",
    "lb100_gpt-5.4-nano_oraclefull_seed0": "gpt-5-4-nano",
    "lb100_gpt5nano_3cond_seed0":         "gpt-5-4-nano",
    "lb100_gpt5nano_oraclefull_seed0":    "gpt-5-nano",
    "lb100_gpt-oss-120b_seed0":           "gpt-oss-120b",
    "lb100_gpt-oss-20b_seed0":            "gpt-oss-20b",
    "lb100_g3flash_3cond_seed0":          "gemini-3-flash-preview",
    "lb100_gemini3flash_oraclefull_seed0": "gemini-3-flash-preview",
    "lb100_g31lite_3cond_seed0":          "gemini-3-1-flash-lite-preview",
    "lb100_gemini31lite_oraclefull_seed0": "gemini-3-1-flash-lite-preview",
    "lb100_gemini-3.1-pro-preview_seed0":  "gemini-3-1-pro-preview",
    "lb100_gemini25pro_oraclefull_seed0":  "gemini-2-5-pro",
    "lb100_gemma4-31b_seed0":             "gemma-4-31b",
    "lb100_qwen3-30b-a3b-or_seed0":       "qwen3-30b-a3b",
    "lb100_qwen3-32b-or_seed0":           "qwen3-32b",
    "lb100_qwen3-14b-or_seed0":           "qwen3-14b",
    "lb100_qwen3-8b-or_seed0":            "qwen3-8b",
    "lb100_qwen3-14b_seed0":              "qwen3-14b",
    "lb100_qwen3-8b_seed0":               "qwen3-8b",
    "lb100_qwen3-4b_seed0":               "qwen3-4b",
    "lb100_qwen35-0.8b_seed0":            "qwen3.5-0.8b",
}


def coalesce(model_raw: str, file_stem: str = "") -> str:
    if model_raw in COALESCE:
        return COALESCE[model_raw]
    if model_raw and model_raw != "?":
        return model_raw
    return CHECKPOINT_STEM_TO_MODEL.get(file_stem, "?")


def load_runs(path: Path, is_jsonl: bool):
    stem = path.name.replace(".json.checkpoint.jsonl", "") if is_jsonl else path.name.replace(".json", "")
    fallback = CHECKPOINT_STEM_TO_MODEL.get(stem)
    inferred = None
    runs = []
    if is_jsonl:
        with path.open() as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if inferred is None:
                    inferred = r.get("model") or fallback
                runs.append(r)
    else:
        try:
            d = json.load(path.open())
        except Exception:
            return None, []
        inferred = d.get("model") or fallback
        runs = d.get("runs", []) or []
    return coalesce(inferred or "?", stem), runs


SKIP_TOKENS = ("invalid", "bak", "old", "consolidated", "pre_", "archived", "backup")
files_canon = sorted(glob.glob(str(RES / "lb100_*.json")))
files_canon = [f for f in files_canon if not any(t in f for t in SKIP_TOKENS) and "checkpoint" not in f]
files_ckpt = sorted(glob.glob(str(RES / "lb100_*.checkpoint.jsonl")))
files_ckpt = [f for f in files_ckpt if not any(t in f for t in SKIP_TOKENS)]
all_files = sorted(files_canon + files_ckpt, key=lambda p: Path(p).stat().st_mtime)

# (model, cond, task) -> {pass, error, partial, source}
per_task: dict[tuple[str, str, str], dict] = {}
for f in all_files:
    p = Path(f)
    is_jsonl = f.endswith(".jsonl")
    model, runs = load_runs(p, is_jsonl)
    if not model or model == "?":
        continue
    for r in runs:
        c = r.get("condition", "?")
        t = r.get("task_id", "?")
        if c not in CONDITIONS or t == "?":
            continue
        is_err = bool(r.get("error"))
        is_pass = bool(r.get("pass")) and not is_err
        partial = float(r.get("partial_score") or 0.0) if not is_err else 0.0
        key = (model, c, t)
        prev = per_task.get(key)
        if prev and not prev["error"] and is_err:
            continue
        per_task[key] = {"pass": is_pass, "error": is_err, "partial": partial, "source": p.name}

# Per (model, cond): mean partial over valid runs, plus pass rate, plus n
agg: dict[str, dict[str, dict]] = defaultdict(dict)
for (m, c, _t), rec in per_task.items():
    if rec["error"]:
        continue
    cell = agg[m].setdefault(c, {"sum_partial": 0.0, "passed": 0, "valid_n": 0})
    cell["sum_partial"] += rec["partial"]
    cell["valid_n"] += 1
    if rec["pass"]:
        cell["passed"] += 1

out = {}
for m, cells in agg.items():
    out[m] = {}
    for c in CONDITIONS:
        cell = cells.get(c)
        if cell and cell["valid_n"]:
            out[m][c] = {
                "mean_partial": cell["sum_partial"] / cell["valid_n"],
                "pass_rate": cell["passed"] / cell["valid_n"],
                "valid_n": cell["valid_n"],
            }
        else:
            out[m][c] = {"mean_partial": None, "pass_rate": None, "valid_n": 0}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"computed_at": __import__("datetime").datetime.utcnow().isoformat(),
                            "models": out}, indent=2))

# Display
DISPLAY = [
    ("Gemma 4 31B",            "gemma-4-31b",                    r"\logog"),
    ("GPT-5.4 Mini",           "gpt-5-4-mini",                   r"\logoo"),
    ("Gemini-3.1 Pro",         "gemini-3-1-pro-preview",         r"\logog"),
    ("GPT-5.4",                "gpt-5-4",                        r"\logoo"),
    ("Claude Haiku 4.5",       "claude-haiku-4-5",               r"\logoa"),
    ("Gemini-3 Flash",         "gemini-3-flash-preview",         r"\logog"),
    ("Claude Sonnet 4.6",      "claude-sonnet-4-6",              r"\logoa"),
    ("Claude Opus 4.7",        "claude-opus-4-7",                r"\logoa"),
    ("GPT-5.4 Nano",           "gpt-5-4-nano",                   r"\logoo"),
    ("Gemini-3.1 Flash Lite",  "gemini-3-1-flash-lite-preview",  r"\logog"),
    ("GPT-5 Nano",             "gpt-5-nano",                     r"\logoo"),
]


def fmt_partial(c, threshold_n=50):
    if not c or c["valid_n"] < threshold_n:
        return "--", "--"
    return f"{c['mean_partial']:.3f}", f"{c['pass_rate']*100:.1f}\\%"


# Sort by Full mean_partial desc among rows with full valid_n>=50
def sortkey(r):
    label, mkey, _ = r
    full = out.get(mkey, {}).get("full")
    if not full or full["valid_n"] < 50:
        return (1, 0)
    return (0, -full["mean_partial"])


DISPLAY_SORTED = sorted(DISPLAY, key=sortkey)
print("=== tab:partial-scores body ===\n")
print("Model & Solo partial & Solo pass & Full partial & Full pass \\\\")
print(r"\midrule")
# bold the leading Full partial
max_full = max(
    (out.get(k, {}).get("full") or {}).get("mean_partial") or 0
    for _, k, _ in DISPLAY_SORTED
)
for label, mkey, logo in DISPLAY_SORTED:
    cells = out.get(mkey, {})
    solo = cells.get("oracle")
    full = cells.get("full")
    sp, sr = fmt_partial(solo)
    fp, fr = fmt_partial(full)
    if fp != "--" and abs(float(fp) - max_full) < 0.0005:
        fp = f"\\textbf{{{fp}}}"
    print(f"{logo}~{label:<22} & {sp:>6} & {sr:>7} & {fp:>14} & {fr:>7} \\\\")
print(f"\nWrote {OUT}")
