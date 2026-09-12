#!/usr/bin/env python3
"""Run heterogeneous role ablation: 27 configs × N tasks × 1 seed.

Tests {Planner, Executor, Verifier} × {Haiku 4.5, Gemini-3-flash, GPT-5.4-mini}.

Outputs to shared/role_ablation/:
  - runs/{config}/{task}/seed_0/   : workspace, per-role logs, score
  - results/per_run.jsonl          : append-only checkpoint
  - results/per_config.json        : aggregate per-config
  - results/summary.json           : Pareto / marginals / best-per-tier
  - cost_tracking.json             : actual tokens + USD per role per run
  - logs/{config}_{task}.log       : per-run stdout+stderr

Usage:
    python scripts/run_role_ablation.py --smoke
    python scripts/run_role_ablation.py --full
    python scripts/run_role_ablation.py --resume
    python scripts/run_role_ablation.py --estimate
    python scripts/run_role_ablation.py --config PAEGVO
    python scripts/run_role_ablation.py --task TASK_ID
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
import time
import traceback
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from harness.ablation import AblationCondition, run_ablation_condition
from harness.adapters import create_adapter
from harness.run_all import setup_run, grade_run

# ---------------------------------------------------------------------------
# Model tiers (3 families)
# ---------------------------------------------------------------------------
TIERS: dict[str, str] = {
    # Haiku routed via OpenRouter (Anthropic direct credits exhausted 2026-04-24).
    # OR adapter in harness/adapters/openai_adapter.py pins
    # provider={"order":["anthropic"], allow_fallbacks:False} so requests still
    # hit Anthropic's real API (not Bedrock/GCP), preserving equivalence with
    # seed-0 direct-Anthropic runs.
    "A": "openrouter:anthropic/claude-haiku-4.5",  # Anthropic (via OR)
    "G": "gemini-3-flash-preview",                  # Google (direct)
    "O": "gpt-5.4-mini",                            # OpenAI (direct)
}

ROLES = ("planner", "executor", "verifier")

# Output paths
ROLE_DIR = REPO_ROOT / "shared" / "role_ablation"
TASKS_FILE = ROLE_DIR / "tasks_25.json"
PRICING_FILE = ROLE_DIR / "pricing.json"
RUNS_DIR = ROLE_DIR / "runs"
RESULTS_DIR = ROLE_DIR / "results"
LOGS_DIR = ROLE_DIR / "logs"
LATEX_DIR = ROLE_DIR / "latex"

PER_RUN_JSONL = RESULTS_DIR / "per_run.jsonl"
COST_FILE = ROLE_DIR / "cost_tracking.json"
PER_CONFIG_FILE = RESULTS_DIR / "per_config.json"
SUMMARY_FILE = RESULTS_DIR / "summary.json"

TASKS_DIR = REPO_ROOT / "tasks"


# ---------------------------------------------------------------------------
# Config enumeration
# ---------------------------------------------------------------------------
def build_configs() -> dict[str, dict[str, str]]:
    """Return 27 P{X}E{Y}V{Z} configs where X,Y,Z in {A,G,O}."""
    out: dict[str, dict[str, str]] = {}
    for p, e, v in itertools.product("AGO", repeat=3):
        name = f"P{p}E{e}V{v}"
        out[name] = {
            "planner": TIERS[p],
            "executor": TIERS[e],
            "verifier": TIERS[v],
        }
    return out


ALL_CONFIGS = build_configs()


# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------
def load_pricing() -> dict[str, dict[str, float]]:
    with open(PRICING_FILE) as f:
        doc = json.load(f)
    return doc["models"]


def cost_usd(tokens_in: int, tokens_out: int, model: str, pricing: dict) -> float:
    p = pricing.get(model)
    if not p:
        return 0.0
    return tokens_in * p["input"] / 1e6 + tokens_out * p["output"] / 1e6


# ---------------------------------------------------------------------------
# Checkpoint / resume
# ---------------------------------------------------------------------------
def load_completed() -> set[tuple[str, str, int]]:
    """Load set of (config, task, seed) already completed from per_run.jsonl."""
    done: set[tuple[str, str, int]] = set()
    if not PER_RUN_JSONL.exists():
        return done
    with open(PER_RUN_JSONL) as f:
        for line in f:
            try:
                r = json.loads(line)
                key = (r["config"], r["task_id"], int(r.get("seed", 0)))
                done.add(key)
            except Exception:
                continue
    return done


def append_run(record: dict) -> None:
    PER_RUN_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with open(PER_RUN_JSONL, "a") as f:
        f.write(json.dumps(record, default=str) + "\n")


# ---------------------------------------------------------------------------
# Task loading
# ---------------------------------------------------------------------------
def load_tasks(limit: int | None = None) -> list[str]:
    with open(TASKS_FILE) as f:
        doc = json.load(f)
    ids = [t["task_id"] for t in doc["tasks"]]
    return ids[:limit] if limit else ids


# ---------------------------------------------------------------------------
# Single run
# ---------------------------------------------------------------------------
def run_one(
    config_name: str,
    model_config: dict[str, str],
    task_id: str,
    seed: int,
    max_turns: int,
    max_remediation: int,
    pricing: dict,
) -> dict:
    """Run a single (config, task, seed) and return a record."""
    tasks_dir = str(TASKS_DIR)
    runs_base = str(RUNS_DIR / config_name)
    log_path = LOGS_DIR / f"{config_name}_{task_id}_seed{seed}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    record: dict = {
        "config": config_name,
        "model_config": model_config,
        "task_id": task_id,
        "seed": seed,
        "run_id": "",
        "run_dir": "",
        "pass": False,
        "partial_score": 0.0,
        "elapsed_sec": 0.0,
        "role_usage": {},
        "cost_usd_by_role": {},
        "cost_usd_total": 0.0,
        "turns_total": 0,
        "failure_modes": [],
        "error": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    start = time.time()
    try:
        # Fallback adapter in case any role is missing (shouldn't happen here).
        fallback = create_adapter(model=model_config["executor"], temperature=0.2)
        run_id, run_dir, task_dir = setup_run(task_id, tasks_dir, runs_base, seed=seed)
        record["run_id"] = run_id
        record["run_dir"] = run_dir

        # Tag run_meta.json so post-hoc analysis can identify this run.
        meta_path = os.path.join(run_dir, "run_meta.json")
        if os.path.isfile(meta_path):
            with open(meta_path) as mf:
                meta = json.load(mf)
            meta["condition"] = "role_ablation_hetero"
            meta["model_config"] = model_config
            meta["role_ablation_config"] = config_name
            with open(meta_path, "w") as mf:
                json.dump(meta, mf, indent=2)

        with open(log_path, "w") as logf:
            with redirect_stdout(logf), redirect_stderr(logf):
                orch_result = run_ablation_condition(
                    condition=AblationCondition.HETERO,
                    task_dir=task_dir,
                    run_dir=run_dir,
                    adapter=fallback,
                    max_turns=max_turns,
                    max_remediation=max_remediation,
                    model_config=model_config,
                )

        elapsed = time.time() - start
        score = grade_run(task_id, task_dir, run_dir)
        passed = bool(score.get("pass", False))
        partial = float(score.get("secondary", {}).get(
            "partial_score", 1.0 if passed else 0.0
        ))

        role_usage = getattr(orch_result, "role_usage", {}) or {}
        cost_by_role: dict[str, float] = {}
        for role, u in role_usage.items():
            c = cost_usd(
                int(u.get("input_tokens", 0)),
                int(u.get("output_tokens", 0)),
                u.get("model", ""),
                pricing,
            )
            cost_by_role[role] = round(c, 6)

        record.update({
            "pass": passed,
            "partial_score": partial,
            "elapsed_sec": round(elapsed, 1),
            "role_usage": role_usage,
            "cost_usd_by_role": cost_by_role,
            "cost_usd_total": round(sum(cost_by_role.values()), 6),
            "turns_total": orch_result.total_turns,
            "failure_modes": score.get("failure_modes", []),
        })

    except Exception as e:
        record["error"] = f"{type(e).__name__}: {e}"
        record["traceback"] = traceback.format_exc()
        record["elapsed_sec"] = round(time.time() - start, 1)

    # Persist per-run meta with rich info (role tokens, cost)
    try:
        if record.get("run_dir"):
            meta_path = os.path.join(record["run_dir"], "run_meta.json")
            if os.path.isfile(meta_path):
                with open(meta_path) as mf:
                    meta = json.load(mf)
                meta["role_usage"] = record["role_usage"]
                meta["cost_usd_by_role"] = record["cost_usd_by_role"]
                meta["cost_usd_total"] = record["cost_usd_total"]
                meta["turns_total"] = record["turns_total"]
                meta["pass"] = record["pass"]
                meta["partial_score"] = record["partial_score"]
                with open(meta_path, "w") as mf:
                    json.dump(meta, mf, indent=2)
    except Exception:
        pass

    return record


# ---------------------------------------------------------------------------
# Campaign
# ---------------------------------------------------------------------------
def run_campaign(
    configs: dict[str, dict[str, str]],
    tasks: list[str],
    seed: int,
    max_turns: int,
    max_remediation: int,
    resume: bool,
) -> list[dict]:
    pricing = load_pricing()
    done = load_completed() if resume else set()
    skipped = 0

    records: list[dict] = []
    total = len(configs) * len(tasks)
    idx = 0
    t_start = time.time()
    for cfg_name, mc in configs.items():
        for task_id in tasks:
            idx += 1
            key = (cfg_name, task_id, seed)
            if key in done:
                skipped += 1
                continue
            elapsed_so_far = time.time() - t_start
            remaining = total - idx
            eta = (elapsed_so_far / max(1, idx - skipped)) * remaining if idx > skipped else 0
            print(
                f"[{idx}/{total}] {cfg_name} × {task_id} seed={seed} "
                f"(elapsed={elapsed_so_far/60:.1f}m, ETA={eta/60:.1f}m)",
                flush=True,
            )
            rec = run_one(
                config_name=cfg_name,
                model_config=mc,
                task_id=task_id,
                seed=seed,
                max_turns=max_turns,
                max_remediation=max_remediation,
                pricing=pricing,
            )
            status = "PASS" if rec["pass"] else ("ERR" if rec["error"] else "FAIL")
            cost = rec["cost_usd_total"]
            print(
                f"    {status} partial={rec['partial_score']:.2f} "
                f"cost=${cost:.4f} turns={rec['turns_total']} "
                f"t={rec['elapsed_sec']}s",
                flush=True,
            )
            append_run(rec)
            records.append(rec)
    return records


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------
def aggregate() -> dict:
    """Rebuild per_config.json and summary.json from per_run.jsonl."""
    pricing = load_pricing()
    runs: list[dict] = []
    if PER_RUN_JSONL.exists():
        with open(PER_RUN_JSONL) as f:
            for line in f:
                try:
                    runs.append(json.loads(line))
                except Exception:
                    continue

    # Per config
    per_config: dict[str, dict] = {}
    for cfg_name in ALL_CONFIGS:
        cr = [r for r in runs if r.get("config") == cfg_name]
        total = len(cr)
        if total == 0:
            continue
        passes = sum(1 for r in cr if r.get("pass"))
        avg_partial = sum(r.get("partial_score", 0.0) for r in cr) / total
        total_cost = sum(r.get("cost_usd_total", 0.0) for r in cr)
        total_tokens_in = sum(
            sum(u.get("input_tokens", 0) for u in r.get("role_usage", {}).values())
            for r in cr
        )
        total_tokens_out = sum(
            sum(u.get("output_tokens", 0) for u in r.get("role_usage", {}).values())
            for r in cr
        )
        total_wall = sum(r.get("elapsed_sec", 0.0) for r in cr)
        per_config[cfg_name] = {
            "model_config": ALL_CONFIGS[cfg_name],
            "total_runs": total,
            "passes": passes,
            "success_rate": round(passes / total, 4),
            "avg_partial_score": round(avg_partial, 4),
            "total_cost_usd": round(total_cost, 4),
            "avg_cost_per_task_usd": round(total_cost / total, 6),
            "total_input_tokens": total_tokens_in,
            "total_output_tokens": total_tokens_out,
            "total_wall_sec": round(total_wall, 1),
        }

    # Overall cost tracking
    cost_doc = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "total_runs": len(runs),
        "total_cost_usd": round(sum(r.get("cost_usd_total", 0.0) for r in runs), 4),
        "total_input_tokens": sum(
            sum(u.get("input_tokens", 0) for u in r.get("role_usage", {}).values())
            for r in runs
        ),
        "total_output_tokens": sum(
            sum(u.get("output_tokens", 0) for u in r.get("role_usage", {}).values())
            for r in runs
        ),
        "by_model": {},
        "pricing_used": pricing,
    }
    for r in runs:
        for role, u in r.get("role_usage", {}).items():
            m = u.get("model") or "unknown"
            bm = cost_doc["by_model"].setdefault(
                m, {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "calls": 0}
            )
            bm["input_tokens"] += int(u.get("input_tokens", 0))
            bm["output_tokens"] += int(u.get("output_tokens", 0))
            bm["cost_usd"] += r.get("cost_usd_by_role", {}).get(role, 0.0)
            bm["calls"] += 1
    for m, bm in cost_doc["by_model"].items():
        bm["cost_usd"] = round(bm["cost_usd"], 4)

    PER_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PER_CONFIG_FILE, "w") as f:
        json.dump(per_config, f, indent=2)

    with open(COST_FILE, "w") as f:
        json.dump(cost_doc, f, indent=2)

    summary = {
        "total_runs": len(runs),
        "configs_completed": len(per_config),
        "total_cost_usd": cost_doc["total_cost_usd"],
        "top_configs": sorted(
            [{"config": k, **v} for k, v in per_config.items()],
            key=lambda x: (-x["success_rate"], x["avg_cost_per_task_usd"]),
        )[:10],
    }
    with open(SUMMARY_FILE, "w") as f:
        json.dump(summary, f, indent=2)
    return summary


# ---------------------------------------------------------------------------
# Cost estimator (from smoke data)
# ---------------------------------------------------------------------------
def estimate_full_from_smoke(n_configs: int = 27, n_tasks: int = 25) -> dict:
    """Extrapolate smoke-run per-task cost to full campaign."""
    if not PER_RUN_JSONL.exists():
        return {"error": "No per_run.jsonl found. Run --smoke first."}
    runs: list[dict] = []
    with open(PER_RUN_JSONL) as f:
        for line in f:
            try:
                runs.append(json.loads(line))
            except Exception:
                continue
    if not runs:
        return {"error": "No completed runs in per_run.jsonl."}

    # Per-config average cost (some configs may not be covered in smoke)
    per_cfg: dict[str, list[float]] = {}
    per_cfg_time: dict[str, list[float]] = {}
    for r in runs:
        per_cfg.setdefault(r["config"], []).append(r.get("cost_usd_total", 0.0))
        per_cfg_time.setdefault(r["config"], []).append(r.get("elapsed_sec", 0.0))

    # Mean cost per task observed
    all_costs = [c for vs in per_cfg.values() for c in vs]
    all_times = [t for vs in per_cfg_time.values() for t in vs]
    mean_cost = sum(all_costs) / len(all_costs) if all_costs else 0.0
    mean_time = sum(all_times) / len(all_times) if all_times else 0.0

    # Costs partitioned by the number of API roles of each model in the config
    # Use observed mean as a simple projection. Smoke uses reduced max_turns — scale up.
    smoke_max_turns = 5
    full_max_turns = 20
    turn_scale = full_max_turns / smoke_max_turns  # 4x

    projected_cost_per_task = mean_cost * turn_scale
    projected_time_per_task = mean_time * turn_scale
    total_runs = n_configs * n_tasks
    projected_total_cost = projected_cost_per_task * total_runs
    projected_total_time_serial = projected_time_per_task * total_runs
    projected_total_time_3way = projected_total_time_serial / 3

    return {
        "based_on_smoke_runs": len(runs),
        "smoke_max_turns": smoke_max_turns,
        "full_max_turns": full_max_turns,
        "turn_scale_applied": turn_scale,
        "observed_mean_cost_per_task_usd": round(mean_cost, 4),
        "observed_mean_time_per_task_sec": round(mean_time, 1),
        "projected_cost_per_task_usd": round(projected_cost_per_task, 4),
        "projected_total_cost_usd": round(projected_total_cost, 2),
        "projected_total_cost_range_usd": [
            round(projected_total_cost * 0.7, 2),
            round(projected_total_cost * 1.3, 2),
        ],
        "total_runs_planned": total_runs,
        "projected_wall_serial_hours": round(projected_total_time_serial / 3600, 2),
        "projected_wall_3way_parallel_hours": round(projected_total_time_3way / 3600, 2),
        "per_config_observed": {
            k: {
                "n": len(v),
                "mean_cost_usd": round(sum(v) / len(v), 4),
                "mean_time_sec": round(sum(per_cfg_time[k]) / len(per_cfg_time[k]), 1),
            }
            for k, v in per_cfg.items()
        },
    }


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--smoke", action="store_true", help="3 configs × 2 tasks, max_turns=5")
    mode.add_argument("--full", action="store_true", help="27 configs × N tasks (default 25)")
    mode.add_argument("--estimate", action="store_true", help="Project full-run cost from smoke")
    mode.add_argument("--aggregate", action="store_true", help="Rebuild per_config.json + summary.json")
    ap.add_argument("--resume", action="store_true", help="Skip runs already in per_run.jsonl (modifier for --full)")
    ap.add_argument("--config", type=str, help="Single config name (e.g. PAEGVO)")
    ap.add_argument("--configs", type=str, help="Comma-separated list of configs to run")
    ap.add_argument("--skip-haiku", action="store_true", help="Skip configs that include Haiku ('A') in any role")
    ap.add_argument("--task", type=str, help="Single task id")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-turns", type=int, default=20)
    ap.add_argument("--max-remediation", type=int, default=2)
    ap.add_argument("--n-tasks", type=int, default=None, help="Override task count")
    args = ap.parse_args()

    for d in (ROLE_DIR, RUNS_DIR, RESULTS_DIR, LOGS_DIR, LATEX_DIR):
        d.mkdir(parents=True, exist_ok=True)

    if args.estimate:
        out = estimate_full_from_smoke(n_configs=27, n_tasks=args.n_tasks or 25)
        print(json.dumps(out, indent=2))
        return 0

    if args.aggregate:
        out = aggregate()
        print(json.dumps(out, indent=2))
        return 0

    # Pick configs and tasks
    all_tasks = load_tasks()
    if args.task:
        tasks = [args.task]
    elif args.smoke:
        tasks = all_tasks[:2]  # 2 smoke tasks
    else:
        tasks = all_tasks[: args.n_tasks] if args.n_tasks else all_tasks

    if args.config:
        if args.config not in ALL_CONFIGS:
            print(f"Unknown config: {args.config}", file=sys.stderr)
            return 2
        configs = {args.config: ALL_CONFIGS[args.config]}
    elif args.configs:
        names = [c.strip() for c in args.configs.split(",") if c.strip()]
        missing = [n for n in names if n not in ALL_CONFIGS]
        if missing:
            print(f"Unknown configs: {missing}", file=sys.stderr)
            return 2
        configs = {n: ALL_CONFIGS[n] for n in names}
    elif args.smoke:
        # 3 configs exercising all 3 families
        configs = {k: ALL_CONFIGS[k] for k in ("PAEGVO", "POEAVG", "PGEOVA")}
    else:
        configs = dict(ALL_CONFIGS)

    if args.skip_haiku:
        configs = {k: v for k, v in configs.items() if "A" not in k}
        print(f"Skipping Haiku configs; remaining: {list(configs.keys())}")

    # Parameters
    if args.smoke:
        max_turns = 5
        max_remediation = 0
    else:
        max_turns = args.max_turns
        max_remediation = args.max_remediation

    resume = args.resume

    print(f"Launching {'SMOKE' if args.smoke else 'FULL'} campaign")
    print(f"  configs: {len(configs)} -> {list(configs.keys())[:5]}{'...' if len(configs) > 5 else ''}")
    print(f"  tasks:   {len(tasks)} -> {tasks[:3]}{'...' if len(tasks) > 3 else ''}")
    print(f"  seed={args.seed}, max_turns={max_turns}, max_remediation={max_remediation}")
    print(f"  resume={resume}")
    print(f"  output: {ROLE_DIR}")

    run_campaign(
        configs=configs,
        tasks=tasks,
        seed=args.seed,
        max_turns=max_turns,
        max_remediation=max_remediation,
        resume=resume,
    )

    summary = aggregate()
    print("\n=== Summary ===")
    print(json.dumps(summary, indent=2))
    print(f"\nTotal cost so far: ${summary.get('total_cost_usd', 0):.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
