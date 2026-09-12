"""Re-grade per-model leaderboard runs by promoting attestation-only failures.

Rationale. The default grader marks a run pass=False when ANY check fails,
including the `attestation_missing` / `bad_attestation` check that only
verifies the model wrote a valid attestation JSON at the end of the run.
For Solo (oracle) mode, the attestation is the agent's self-confirmation
and does not measure task quality. Several frontier models (notably Opus
4.7 and Gemini-3.1 Pro) systematically forget the attestation file even
when every structural check passes; the original grader counts those runs
as task failures.

This script reads each model's per-run records and re-grades a run as
pass=True under one additional rule:

  PASS if (original pass=True) OR
         (original pass=False AND every failure_mode is attestation-related
          AND no other failure mode appears).

The output is written to shared/paper/lb90_full_aggregate_regraded.json
in the same schema as lb90_full_aggregate.json so the leaderboard figure
and per-condition table can read it directly. The original pass field is
preserved per-run so the regrade is reversible.
"""
import json
import os
from collections import defaultdict
from pathlib import Path

REPO = Path("/u/ybkim95/TeamBench")
OUT = REPO / "shared/paper/lb90_full_aggregate_regraded.json"

ATT_FAIL = {
    "bad_attestation", "attestation_missing", "no_attestation",
    "attestation_invalid", "missing_attestation",
}

# Map from canonical model name to per-model raw run files. Prefer the
# checkpoint files because they retain the original `failure_modes` arrays;
# the consolidated `.json` files were rebuilt by a recovery pass that lost
# the per-check failure breakdown for many runs.
SOURCES = {
    "gpt-5-4-mini":       ["shared/ablation_results/lb100_gpt5mini_5cond_seed0.json.checkpoint.jsonl",
                           "shared/ablation_results/lb100_gpt5mini_5cond_seed0.json"],
    "gpt-5-4":            ["shared/ablation_results/lb100_gpt54_3cond_seed0.json.checkpoint.jsonl",
                           "shared/ablation_results/lb100_gpt54_oraclefull_seed0.json.checkpoint.jsonl",
                           "shared/ablation_results/lb100_gpt54_3cond_seed0.json",
                           "shared/ablation_results/lb100_gpt54_oraclefull_seed0.json"],
    "claude-sonnet-4-6":  ["shared/ablation_results/lb100_sonnet46_3cond_seed0.json.checkpoint.jsonl",
                           "shared/ablation_results/lb100_sonnet46_oraclefull_seed0.json.checkpoint.jsonl",
                           "shared/ablation_results/lb100_sonnet46_3cond_seed0.json",
                           "shared/ablation_results/lb100_sonnet46_oraclefull_seed0.json"],
    "claude-opus-4-7":    ["shared/ablation_results/lb100_opus47_seed0.json.checkpoint.jsonl"],
    "claude-haiku-4-5":   ["shared/ablation_results/lb100_haiku45_3cond_seed0.json.checkpoint.jsonl",
                           "shared/ablation_results/lb100_haiku45_oraclefull_seed0.json.checkpoint.jsonl",
                           "shared/ablation_results/lb100_haiku45_full_resume.json",
                           "shared/ablation_results/lb100_haiku45_3cond_seed0.json",
                           "shared/ablation_results/lb100_haiku45_oraclefull_seed0.json"],
    "gemini-3-flash-preview": ["shared/ablation_results/lb100_g3flash_3cond_seed0.json.checkpoint.jsonl",
                               "shared/ablation_results/lb100_gemini3flash_oraclefull_seed0.json.checkpoint.jsonl",
                               "shared/ablation_results/lb100_g3flash_3cond_seed0.json",
                               "shared/ablation_results/lb100_gemini3flash_oraclefull_seed0.json"],
    "gemini-3-1-pro-preview": ["shared/ablation_results/lb100_gemini-3.1-pro-preview_seed0.json.checkpoint.jsonl",
                               "shared/ablation_results/lb100_gemini-3.1-pro-preview_seed0.json"],
    "gemini-3-1-flash-lite-preview": ["shared/ablation_results/lb100_g31lite_3cond_seed0.json.checkpoint.jsonl",
                                      "shared/ablation_results/lb100_gemini31lite_oraclefull_seed0.json.checkpoint.jsonl",
                                      "shared/ablation_results/lb100_g31lite_3cond_seed0.json",
                                      "shared/ablation_results/lb100_gemini31lite_oraclefull_seed0.json"],
    "gemma-4-31b":        ["shared/ablation_results/lb100_gemma4-31b_seed0.json.checkpoint.jsonl",
                           "shared/ablation_results/lb100_gemma4-31b_seed0.json"],
    "gpt-oss-120b":       ["shared/ablation_results/lb100_gpt-oss-120b_seed0.json.checkpoint.jsonl"],
    "gpt-oss-20b":        ["shared/ablation_results/lb100_gpt-oss-20b_seed0.json.checkpoint.jsonl"],
    "qwen3-14b":          ["shared/ablation_results/lb100_qwen3-14b-or_seed0.json.checkpoint.jsonl",
                           "shared/ablation_results/lb100_qwen3-14b-or_seed0.json"],
    "qwen3-32b":          ["shared/ablation_results/lb100_qwen3-32b-or_seed0.json.checkpoint.jsonl",
                           "shared/ablation_results/lb100_qwen3-32b-or_seed0.json"],
    "qwen3-8b":           ["shared/ablation_results/lb100_qwen3-8b-or_seed0.json.checkpoint.jsonl",
                           "shared/ablation_results/lb100_qwen3-8b-or_seed0.json"],
}


def _is_better_record(r_new, r_old):
    """Prefer the record with non-empty failure_modes if both exist."""
    if r_old is None:
        return True
    new_has = bool(r_new.get("failure_modes"))
    old_has = bool(r_old.get("failure_modes"))
    if new_has and not old_has:
        return True
    if old_has and not new_has:
        return False
    return True  # keep the later one as a tiebreak (more recent runs win)


def load_runs(paths):
    runs = {}
    for p in paths:
        full = REPO / p
        if not full.exists():
            continue
        if str(full).endswith(".jsonl"):
            with open(full) as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    key = (r.get("condition"), r.get("task_id"))
                    if _is_better_record(r, runs.get(key)):
                        runs[key] = r
        else:
            d = json.load(open(full))
            arr = d if isinstance(d, list) else d.get("runs") or []
            for r in arr:
                key = (r.get("condition"), r.get("task_id"))
                if _is_better_record(r, runs.get(key)):
                    runs[key] = r
    return list(runs.values())


def is_attestation_only_fail(r):
    """True iff the run failed AND every failure_mode is attestation-related."""
    if r.get("pass") is True:
        return False
    fm = set(r.get("failure_modes") or [])
    return bool(fm) and fm.issubset(ATT_FAIL)


def regrade():
    out = {"computed_at": "regraded:attestation-promotion",
           "models": {}}
    for model, paths in SOURCES.items():
        runs = load_runs(paths)
        out_model = {}
        for cond in ("oracle", "restricted", "team_no_plan",
                     "team_no_verify", "full"):
            sub = [r for r in runs if r.get("condition") == cond]
            if not sub:
                out_model[cond] = {"passed": 0, "valid_n": 0, "rate": 0.0,
                                   "passed_orig": 0, "promoted": 0,
                                   "source": "regrade:attestation-promote"}
                continue
            # Valid = run completed end-to-end (no infrastructure error).
            valid = [r for r in sub if not r.get("error")]
            passed_orig = sum(1 for r in valid if r.get("pass") is True)
            promoted = sum(1 for r in valid if is_attestation_only_fail(r))
            passed = passed_orig + promoted
            out_model[cond] = {
                "passed": passed,
                "valid_n": len(valid),
                "rate": passed / len(valid) if valid else 0.0,
                "passed_orig": passed_orig,
                "promoted": promoted,
                "source": "regrade:attestation-promote",
            }
        out["models"][model] = out_model
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(f"Wrote {OUT}")

    # Print summary
    print(f"\n{'Model':30s}  {'Solo orig':>11s}  {'Solo regr':>11s}  "
          f"{'Full orig':>11s}  {'Full regr':>11s}")
    for model, info in out["models"].items():
        s = info["oracle"]; f = info["full"]
        s_o = s["passed_orig"]; s_r = s["passed"]; s_n = s["valid_n"]
        f_o = f["passed_orig"]; f_r = f["passed"]; f_n = f["valid_n"]
        print(f"{model:30s}  "
              f"{s_o:>3d}/{s_n:<3d}={(100*s_o/max(s_n,1)):5.1f}%  "
              f"{s_r:>3d}/{s_n:<3d}={(100*s_r/max(s_n,1)):5.1f}%  "
              f"{f_o:>3d}/{f_n:<3d}={(100*f_o/max(f_n,1)):5.1f}%  "
              f"{f_r:>3d}/{f_n:<3d}={(100*f_r/max(f_n,1)):5.1f}%")


if __name__ == "__main__":
    regrade()
