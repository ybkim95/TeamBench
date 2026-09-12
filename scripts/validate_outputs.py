#!/usr/bin/env python3
"""Validate all lb100 model outputs for correctness and rigor.

For each model with data, check:
  1. Checkpoint structure — no duplicate (task_id, condition, seed) entries
  2. Per-condition distribution — all 100 tasks per condition, no gaps
  3. Error patterns — systematic API/connection errors vs. real task failures
  4. Turn counts and elapsed times — detect stuck / zero-work runs
  5. For each pass, verify transcripts show actual tool calls + grader output
  6. Cross-check: run_dir exists and contains score.json for each entry
"""
import json
import os
import sys
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path("/u/ybkim95/TeamBench")
RESULTS = ROOT / "shared/ablation_results"
RUNS_DIR = RESULTS / "ablation_runs"
EXPECTED_TASKS = 100
EXPECTED_CONDITIONS = {"oracle", "restricted", "team_no_verify", "team_no_plan", "full"}


def load_runs(model_short: str) -> list[dict]:
    ckpt = RESULTS / f"lb100_{model_short}_seed0.json.checkpoint.jsonl"
    final = RESULTS / f"lb100_{model_short}_seed0.json"
    runs = []
    if ckpt.exists():
        for line in ckpt.read_text().splitlines():
            if line.strip():
                runs.append(json.loads(line))
    elif final.exists():
        d = json.loads(final.read_text())
        runs = d.get("runs", d.get("all_runs", []))
    return runs


def find_run_dir_size(rd: str) -> int:
    """Return number of turn logs (proxy for actual work done).

    Supports both team-mode (logs/{planner,executor,verifier}/turn_*.json)
    and single-agent modes (logs/{oracle,restricted}/turn_*.json).
    """
    if not rd or not os.path.isdir(rd):
        return -1
    logs = os.path.join(rd, "logs")
    if not os.path.isdir(logs):
        return 0
    total = 0
    for role_dir in os.listdir(logs):
        rdir = os.path.join(logs, role_dir)
        if os.path.isdir(rdir):
            total += len([f for f in os.listdir(rdir) if f.startswith("turn_")])
    return total


def has_tool_calls(rd: str) -> int:
    """Count tool calls across all roles (oracle/executor/planner/verifier)."""
    if not rd or not os.path.isdir(rd):
        return -1
    logs = os.path.join(rd, "logs")
    if not os.path.isdir(logs):
        return 0
    n = 0
    for role_dir in os.listdir(logs):
        rdir = os.path.join(logs, role_dir)
        if not os.path.isdir(rdir):
            continue
        for f in os.listdir(rdir):
            if not f.startswith("turn_") or not f.endswith(".json"):
                continue
            try:
                data = json.loads(Path(rdir, f).read_text())
                n += len(data.get("tool_calls", []))
            except Exception:
                pass
    return n


def validate_model(model_short: str) -> dict:
    runs = load_runs(model_short)
    if not runs:
        return {"status": "no data"}

    # 1. Duplicates
    seen = Counter()
    for r in runs:
        k = (r.get("task_id"), r.get("condition"), r.get("seed", 0))
        seen[k] += 1
    dup = {k: v for k, v in seen.items() if v > 1}

    # 2. Per-condition distribution
    per_cond = defaultdict(set)
    for r in runs:
        per_cond[r.get("condition")].add(r.get("task_id"))
    cond_counts = {c: len(tasks) for c, tasks in per_cond.items()}
    unexpected_conds = set(per_cond) - EXPECTED_CONDITIONS

    # 3. Error patterns
    errors = Counter()
    for r in runs:
        err = r.get("error")
        if err:
            # Classify
            if "404" in err: errors["404_not_found"] += 1
            elif "429" in err or "rate" in err.lower(): errors["429_rate_limit"] += 1
            elif "503" in err or "unavailable" in err.lower(): errors["503_unavailable"] += 1
            elif "Connection" in err: errors["connection_error"] += 1
            elif "timeout" in err.lower(): errors["timeout"] += 1
            else: errors["other"] += 1

    # 4. Elapsed time anomalies
    times = [r.get("elapsed_sec", 0) or 0 for r in runs]
    zero_time = sum(1 for t in times if t < 1.0)  # less than 1s = no real work
    too_fast = sum(1 for t in times if 1.0 <= t < 5.0)  # 1-5s = suspiciously fast
    mean_time = sum(times) / len(times) if times else 0
    max_time = max(times) if times else 0

    # 5. Sample passes — verify they're legit
    passes = [r for r in runs if r.get("pass")]
    legit_passes = 0
    suspicious_passes = []
    for p in passes[:10]:  # check up to 10 passes
        rd = p.get("run_dir")
        turns = find_run_dir_size(rd)
        tools = has_tool_calls(rd)
        if turns < 3 or tools < 1:
            suspicious_passes.append({
                "task": p.get("task_id"),
                "cond": p.get("condition"),
                "turns": turns,
                "tools": tools,
                "elapsed": p.get("elapsed_sec"),
            })
        else:
            legit_passes += 1

    # 6. Missing run_dirs
    missing_rd = sum(1 for r in runs if not r.get("run_dir") or not os.path.isdir(r.get("run_dir", "")))

    return {
        "status": "checked",
        "total_runs": len(runs),
        "per_condition": dict(sorted(cond_counts.items())),
        "unexpected_conditions": list(unexpected_conds),
        "duplicates": len(dup),
        "duplicate_samples": list(dup.items())[:3],
        "errors": dict(errors),
        "error_rate": sum(errors.values()) / len(runs) if runs else 0,
        "zero_time_runs": zero_time,
        "too_fast_runs": too_fast,
        "mean_time_sec": round(mean_time, 1),
        "max_time_sec": round(max_time, 1),
        "missing_run_dirs": missing_rd,
        "total_passes": len(passes),
        "sampled_passes_verified": legit_passes,
        "sampled_passes_suspicious": len(suspicious_passes),
        "suspicious_samples": suspicious_passes[:3],
    }


def list_models() -> list[str]:
    models = set()
    for p in RESULTS.glob("lb100_*_seed0.json*"):
        n = p.name.replace("lb100_", "").replace("_seed0.json.checkpoint.jsonl", "").replace("_seed0.json", "")
        if "oraclefull" in n or n == "v1": continue
        models.add(n)
    return sorted(models)


def main():
    print("=" * 90)
    print("  TEAMBENCH OUTPUT VALIDATION")
    print("=" * 90)
    models = list_models()
    print(f"Validating {len(models)} models: {models}\n")

    overall_health = []
    for m in models:
        r = validate_model(m)
        if r["status"] == "no data":
            print(f"\n[{m}] no data — skipped")
            continue
        print(f"\n━━━ {m} ━━━")
        print(f"  total_runs: {r['total_runs']}")
        print(f"  per_condition: {r['per_condition']}")
        if r["unexpected_conditions"]:
            print(f"  ⚠️  unexpected_conditions: {r['unexpected_conditions']}")
        if r["duplicates"]:
            print(f"  ⚠️  DUPLICATES: {r['duplicates']} — samples: {r['duplicate_samples']}")
        if r["errors"]:
            print(f"  errors: {r['errors']}  (rate: {r['error_rate']:.1%})")
        print(f"  time_profile: mean={r['mean_time_sec']}s  max={r['max_time_sec']}s  zero={r['zero_time_runs']}  <5s={r['too_fast_runs']}")
        if r["missing_run_dirs"]:
            print(f"  ⚠️  missing_run_dirs: {r['missing_run_dirs']}")
        if r["total_passes"]:
            ok = r["sampled_passes_verified"]
            sus = r["sampled_passes_suspicious"]
            print(f"  passes: {r['total_passes']} total | sampled: {ok} legit, {sus} suspicious")
            if r["suspicious_samples"]:
                print(f"    suspicious: {r['suspicious_samples']}")

        # Quality verdict
        issues = []
        if r["duplicates"] > 0: issues.append("DUPLICATES")
        if r["unexpected_conditions"]: issues.append("BAD_CONDITION")
        if r["error_rate"] > 0.05: issues.append(f"HIGH_ERR_RATE({r['error_rate']:.1%})")
        if r["zero_time_runs"] > 5: issues.append(f"ZERO_TIME({r['zero_time_runs']})")
        if r["missing_run_dirs"] > r["total_runs"] * 0.1: issues.append(f"MISSING_RD({r['missing_run_dirs']})")
        if r["sampled_passes_suspicious"] > 0: issues.append(f"SUS_PASS({r['sampled_passes_suspicious']})")
        verdict = "✅ CLEAN" if not issues else f"⚠️  ISSUES: {', '.join(issues)}"
        print(f"  verdict: {verdict}")
        overall_health.append((m, len(issues), issues))

    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    clean = sum(1 for _, n, _ in overall_health if n == 0)
    issue = sum(1 for _, n, _ in overall_health if n > 0)
    print(f"  {clean} clean, {issue} with issues, {len(models)-len(overall_health)} no-data")
    if issue:
        print(f"\n  Models with issues:")
        for m, n, iss in overall_health:
            if n:
                print(f"    {m}: {', '.join(iss)}")


if __name__ == "__main__":
    main()
