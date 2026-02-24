"""
TeamBench multi-model batch runner.

Runs all task x seed x model combinations with parallel execution support.
Supports checkpoint/resume for long evaluation campaigns.

Usage:
    python -m harness.batch_runner --models gemini-2.5-flash --seeds 0 1 2
    python -m harness.batch_runner --models gemini-2.5-flash gpt-4o --tasks S1_hidden_spec --seeds 0 1 2 3 4
    python -m harness.batch_runner --resume shared/batch_campaign/
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from harness.run_all import setup_run, grade_run, discover_tasks


def create_adapter(model_name: str, **kwargs):
    """Factory function for model adapters."""
    if "gemini" in model_name.lower():
        from harness.gemini_adapter import GeminiAdapter
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        return GeminiAdapter(api_key=api_key, model=model_name, **kwargs)
    elif "gpt" in model_name.lower() or "o1" in model_name.lower() or "o3" in model_name.lower():
        try:
            from harness.adapters.openai_adapter import OpenAIAdapter
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            return OpenAIAdapter(api_key=api_key, model=model_name, **kwargs)
        except ImportError:
            raise ImportError(f"OpenAI adapter not yet implemented. Install with: pip install openai")
    elif "claude" in model_name.lower():
        try:
            from harness.adapters.anthropic_adapter import AnthropicAdapter
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            return AnthropicAdapter(api_key=api_key, model=model_name, **kwargs)
        except ImportError:
            raise ImportError(f"Anthropic adapter not yet implemented. Install with: pip install anthropic")
    else:
        raise ValueError(f"Unknown model family: {model_name}. Supported: gemini-*, gpt-*, claude-*")


def load_checkpoint(campaign_dir: str) -> set[str]:
    """Load completed run keys from checkpoint."""
    completed = set()
    checkpoint_path = os.path.join(campaign_dir, "checkpoint.jsonl")
    if os.path.isfile(checkpoint_path):
        with open(checkpoint_path, "r") as f:
            for line in f:
                entry = json.loads(line.strip())
                key = f"{entry['model']}:{entry['task_id']}:{entry['seed']}"
                completed.add(key)
    return completed


def save_checkpoint(campaign_dir: str, entry: dict) -> None:
    """Append a completed run to the checkpoint file."""
    checkpoint_path = os.path.join(campaign_dir, "checkpoint.jsonl")
    with open(checkpoint_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="TeamBench multi-model batch runner")
    ap.add_argument("--models", nargs="+", required=True, help="Model names (e.g., gemini-2.5-flash gpt-4o)")
    ap.add_argument("--tasks", nargs="*", default=None, help="Specific tasks (default: all)")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2], help="Seeds to evaluate")
    ap.add_argument("--tasks-dir", default="tasks", help="Tasks directory")
    ap.add_argument("--campaign-dir", default="shared/campaigns", help="Campaign output directory")
    ap.add_argument("--max-turns", type=int, default=20, help="Max turns per phase")
    ap.add_argument("--max-remediation", type=int, default=2, help="Max remediation loops")
    ap.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    ap.add_argument("--dry-run", action="store_true", help="Show what would run without executing")
    args = ap.parse_args()

    tasks_dir = os.path.abspath(args.tasks_dir)
    task_names = args.tasks or discover_tasks(tasks_dir)

    # Create campaign directory
    if args.resume and os.path.isdir(args.campaign_dir):
        campaign_dir = args.campaign_dir
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        campaign_dir = os.path.join(args.campaign_dir, f"campaign_{timestamp}")
    os.makedirs(campaign_dir, exist_ok=True)

    # Load checkpoint
    completed = load_checkpoint(campaign_dir) if args.resume else set()

    # Build run matrix
    runs = []
    for model in args.models:
        for task in task_names:
            for seed in args.seeds:
                key = f"{model}:{task}:{seed}"
                if key not in completed:
                    runs.append({"model": model, "task": task, "seed": seed, "key": key})

    total = len(runs)
    skipped = len(completed)

    print(f"TeamBench Multi-Model Batch Runner")
    print(f"{'=' * 60}")
    print(f"  Models:  {args.models}")
    print(f"  Tasks:   {len(task_names)}")
    print(f"  Seeds:   {args.seeds}")
    print(f"  Total:   {total} runs ({skipped} skipped from checkpoint)")
    print(f"  Campaign: {campaign_dir}")
    print(f"{'=' * 60}")

    if args.dry_run:
        for r in runs:
            print(f"  WOULD RUN: {r['model']} x {r['task']} x seed={r['seed']}")
        return

    # Save campaign config
    config = {
        "models": args.models,
        "tasks": task_names,
        "seeds": args.seeds,
        "max_turns": args.max_turns,
        "max_remediation": args.max_remediation,
        "started": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(campaign_dir, "config.json"), "w") as f:
        json.dump(config, f, indent=2)

    # Execute runs
    all_results = []
    passed = 0

    for i, run in enumerate(runs, 1):
        model, task, seed = run["model"], run["task"], run["seed"]
        print(f"\n[{i}/{total}] {model} x {task} (seed={seed})")

        start_time = time.time()
        try:
            # Setup workspace with seed
            runs_dir = os.path.join(campaign_dir, "runs")
            run_id, run_dir, task_dir_abs = setup_run(task, tasks_dir, runs_dir, seed=seed)

            # Run orchestrator
            from harness.orchestrator import TaskOrchestrator
            adapter = create_adapter(model)
            orchestrator = TaskOrchestrator(
                task_dir=task_dir_abs,
                run_dir=run_dir,
                adapter=adapter,
                max_turns_per_phase=args.max_turns,
                max_remediation_loops=args.max_remediation,
            )
            orch_result = orchestrator.run()
            elapsed = time.time() - start_time

            # Grade
            score = grade_run(task, task_dir_abs, run_dir)

            # Record result
            usage = adapter.get_usage() if hasattr(adapter, "get_usage") else {}
            result = {
                "model": model,
                "task_id": task,
                "seed": seed,
                "run_id": run_id,
                "pass": score.get("pass", False),
                "partial_score": score.get("secondary", {}).get("partial_score"),
                "agent_verdict": orch_result.verdict,
                "total_turns": orch_result.total_turns,
                "remediation_loops": orch_result.remediation_loops,
                "elapsed_sec": round(elapsed, 1),
                "token_usage": usage,
                "failure_modes": score.get("failure_modes", []),
            }

            if score.get("pass"):
                passed += 1

            # Save per-run meta
            meta_path = os.path.join(run_dir, "meta.json")
            with open(meta_path, "w") as f:
                json.dump(result, f, indent=2)

            status = "PASS" if score.get("pass") else "FAIL"
            print(f"  {status} ({elapsed:.1f}s, {orch_result.total_turns} turns)")

        except Exception as e:
            elapsed = time.time() - start_time
            result = {
                "model": model,
                "task_id": task,
                "seed": seed,
                "pass": False,
                "error": str(e),
                "elapsed_sec": round(elapsed, 1),
            }
            print(f"  ERROR: {e}")

        all_results.append(result)
        save_checkpoint(campaign_dir, result)

    # Write final results
    completed_count = len(all_results)
    final = {
        "campaign_dir": campaign_dir,
        "completed": datetime.now(timezone.utc).isoformat(),
        "total_runs": completed_count,
        "passed": passed,
        "success_rate": round(passed / max(1, completed_count), 4),
        "results": all_results,
    }
    with open(os.path.join(campaign_dir, "results.json"), "w") as f:
        json.dump(final, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  CAMPAIGN COMPLETE")
    print(f"  Total: {completed_count} | Passed: {passed} | Rate: {passed/max(1,completed_count):.1%}")
    print(f"  Results: {campaign_dir}/results.json")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
