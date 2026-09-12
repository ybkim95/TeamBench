"""Proper TeamBench-100 aggregator.

For each (model, condition), takes the maximum valid-n across all sources
(canonical .json files + .checkpoint.jsonl files), keeping the corresponding
pass count. Coalesces sonnet/opus/qwen aliases. Maps checkpoint files whose
records lack a 'model' field by file-stem.

Outputs:
  shared/paper/lb100_full_aggregate.json
"""
from __future__ import annotations

import glob
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path("/u/ybkim95/TeamBench")
RES = ROOT / "shared" / "ablation_results"
OUT = ROOT / "shared" / "paper" / "lb100_full_aggregate.json"

CONDITIONS = ("oracle", "restricted", "team_no_plan", "team_no_verify", "full")

# Canonical model keys (after coalescing). All aliases below map to one key.
COALESCE = {
    # all anthropic-direct + openrouter routes for the same model -> single key
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

# For checkpoint files where line records lack a 'model' field, map by stem.
# All lb100 checkpoint files in shared/ablation_results store the per-line
# records WITHOUT a model field, so this mapping is required to attribute them.
CHECKPOINT_STEM_TO_MODEL = {
    # --- Anthropic ---
    "lb100_haiku45_3cond_seed0":          "claude-haiku-4-5",
    "lb100_haiku45_oraclefull_seed0":     "claude-haiku-4-5",
    "lb100_haiku45_full_resume":          "claude-haiku-4-5",
    "lb100_sonnet46_3cond_seed0":         "claude-sonnet-4-6",
    "lb100_sonnet46_oraclefull_seed0":    "claude-sonnet-4-6",
    "lb100_sonnet46_full_resume":         "claude-sonnet-4-6",
    "lb100_sonnet46_full_resume2":        "claude-sonnet-4-6",
    "lb100_sonnet46_full_resume3":        "claude-sonnet-4-6",
    "lb100_opus47_seed0":                 "claude-opus-4-7",
    # --- OpenAI ---
    "lb100_gpt54_3cond_seed0":            "gpt-5-4",
    "lb100_gpt54_oraclefull_seed0":       "gpt-5-4",
    "lb100_gpt5mini_5cond_seed0":         "gpt-5-4-mini",
    "lb100_gpt-5.4-mini_oraclefull_seed0": "gpt-5-4-mini",
    "lb100_gpt-5.4-nano_oraclefull_seed0": "gpt-5-4-nano",
    "lb100_gpt5nano_3cond_seed0":         "gpt-5-4-nano",   # canonical .json has model=gpt-5.4-nano
    "lb100_gpt5nano_oraclefull_seed0":    "gpt-5-nano",     # canonical .json has model=gpt-5-nano
    "lb100_gpt-oss-120b_seed0":           "gpt-oss-120b",
    "lb100_gpt-oss-20b_seed0":            "gpt-oss-20b",
    # --- Google ---
    "lb100_g3flash_3cond_seed0":          "gemini-3-flash-preview",
    "lb100_gemini3flash_oraclefull_seed0": "gemini-3-flash-preview",
    "lb100_g31lite_3cond_seed0":          "gemini-3-1-flash-lite-preview",
    "lb100_gemini31lite_oraclefull_seed0": "gemini-3-1-flash-lite-preview",
    "lb100_gemini-3.1-pro-preview_seed0":  "gemini-3-1-pro-preview",
    "lb100_gemini25pro_oraclefull_seed0":  "gemini-2-5-pro",
    "lb100_gemma4-31b_seed0":             "gemma-4-31b",
    # --- Alibaba (Qwen) ---
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
    """Return canonical model key, falling back to checkpoint stem map."""
    if model_raw in COALESCE:
        return COALESCE[model_raw]
    if model_raw and model_raw != "?":
        return model_raw  # unknown but at least non-empty
    if file_stem in CHECKPOINT_STEM_TO_MODEL:
        return CHECKPOINT_STEM_TO_MODEL[file_stem]
    return "?"


def load_one_source(path: Path, is_jsonl: bool):
    """Yield (cond, passed, errored) records and the inferred model key."""
    stem = path.name
    if is_jsonl:
        stem = stem.replace(".json.checkpoint.jsonl", "")
    else:
        stem = stem.replace(".json", "")
    fallback_model = CHECKPOINT_STEM_TO_MODEL.get(stem)
    runs = []
    inferred_model = None
    if is_jsonl:
        with path.open() as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if inferred_model is None:
                    inferred_model = r.get("model") or fallback_model
                runs.append(r)
    else:
        try:
            d = json.load(path.open())
        except Exception:
            return None, []
        inferred_model = d.get("model") or fallback_model
        runs = d.get("runs", []) or []
    inferred_model = coalesce(inferred_model or "?", stem)
    return inferred_model, runs


# Walk every source and collect per (model, cond, task_id) the latest valid run.
# Source priority for tie-breaking: file mtime descending (newer wins).
# Errored runs are dropped UNLESS no other source for that (model, cond, task).
SKIP_TOKENS = ("invalid", "bak", "old", "consolidated", "pre_", "archived", "backup")
files_canonical = sorted(glob.glob(str(RES / "lb100_*.json")))
files_canonical = [f for f in files_canonical
                   if not any(t in f for t in SKIP_TOKENS) and "checkpoint" not in f]
files_checkpoint = sorted(glob.glob(str(RES / "lb100_*.checkpoint.jsonl")))
files_checkpoint = [f for f in files_checkpoint
                    if not any(t in f for t in SKIP_TOKENS)]

# Order all sources oldest-first so that later (newer) writes overwrite earlier
# ones at the (model, cond, task) level.
all_files = sorted(files_canonical + files_checkpoint, key=lambda p: Path(p).stat().st_mtime)

# (model, cond, task_id) -> {"pass": bool, "error": bool, "source": str}
per_task: dict[tuple[str, str, str], dict] = {}
source_log: dict[str, int] = defaultdict(int)

for f in all_files:
    p = Path(f)
    is_jsonl = f.endswith(".jsonl")
    model, runs = load_one_source(p, is_jsonl)
    if not model or model == "?":
        continue
    for r in runs:
        c = r.get("condition", "?")
        t = r.get("task_id", "?")
        if c not in CONDITIONS or t == "?":
            continue
        is_err = bool(r.get("error"))
        is_pass = bool(r.get("pass")) and not is_err
        key = (model, c, t)
        prev = per_task.get(key)
        # Always overwrite with newer source, except if the new record is
        # errored and we already have a non-errored result.
        if prev and not prev["error"] and is_err:
            continue
        per_task[key] = {"pass": is_pass, "error": is_err, "source": p.name}
        source_log[p.name] += 1

# Now compute (model, cond) -> [valid_passed, valid_n] excluding errored
final_cells: dict[tuple[str, str], list] = defaultdict(lambda: [0, 0, set()])
for (m, c, t), rec in per_task.items():
    if rec["error"]:
        continue
    final_cells[(m, c)][1] += 1
    if rec["pass"]:
        final_cells[(m, c)][0] += 1
    final_cells[(m, c)][2].add(rec["source"])
final_cells = {k: [v[0], v[1], "+".join(sorted(v[2])[:3])]
               for k, v in final_cells.items()}

# Build per-model dict
out: dict[str, dict] = {}
all_models = sorted({m for (m, _) in final_cells.keys()})
for m in all_models:
    out[m] = {}
    for c in CONDITIONS:
        cell = final_cells.get((m, c))
        if cell:
            p, n, src = cell
            out[m][c] = {"passed": p, "valid_n": n, "rate": p / n if n else None,
                         "source": src}
        else:
            out[m][c] = {"passed": 0, "valid_n": 0, "rate": None, "source": None}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"computed_at": __import__("datetime").datetime.utcnow().isoformat(),
                            "models": out}, indent=2))

# Print
print(f"Aggregated {len(all_models)} models from {len(source_log)} source files, "
      f"{len(per_task)} unique (model, cond, task) records.\n")
print(f"{'Model':<22}{'oracle':>14}{'restr.':>14}{'noplan':>14}{'noeval':>14}{'full':>14}")
print("-" * 110)
def fmt_cell(cell):
    if cell.get("valid_n", 0) == 0:
        return "      0/0"
    return f"  {cell['passed']:>3}/{cell['valid_n']:<3}={cell['rate']*100:>5.1f}%"
for m in all_models:
    cells = out[m]
    parts = [fmt_cell(cells[c]) for c in CONDITIONS]
    print(f"{m[:21]:<22}{parts[0]:>14}{parts[1]:>14}{parts[2]:>14}{parts[3]:>14}{parts[4]:>14}")

# Source attribution log
print("\n=== source winning per (model, cond) — flag mismatches ===\n")
for m in all_models:
    cells = out[m]
    sources = {c: cells[c]["source"] for c in CONDITIONS if cells[c]["valid_n"] > 0}
    types = set("checkpoint" if (s or "").endswith(".jsonl") else "canonical" for s in sources.values())
    if len(types) > 1 or any("checkpoint" in (s or "") for s in sources.values()):
        print(f"  {m}:")
        for c, s in sources.items():
            tag = "ckpt" if (s or "").endswith(".jsonl") else "canon"
            print(f"    {c:<18} <- {tag:<5} {s}")
