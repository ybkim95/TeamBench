"""
TeamBench agent driver — run a multi-agent evaluation on a single task.

Usage:
    python -m harness.run_agent --task S1_hidden_spec --model gemini-2.5-flash
    python -m harness.run_agent --task S1_hidden_spec --model gemini-2.5-pro --max-turns 25
    python -m harness.run_agent --task all    # Run all tasks sequentially
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from harness.run_all import setup_run, grade_run, discover_tasks
from harness.gemini_adapter import GeminiAdapter
from harness.orchestrator import TaskOrchestrator


def load_api_key() -> str:
    """Load Gemini API key from environment or .env file."""
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key

    # Try loading from common .env locations
    for env_path in [
        os.path.expanduser("~/CoDaS_v4/.env"),
        os.path.join(os.getcwd(), ".env"),
    ]:
        if os.path.isfile(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")

    print("ERROR: GEMINI_API_KEY not found.")
    print("Set it via environment variable or in .env file.")
    sys.exit(1)


def run_single_task(
    task_name: str,
    tasks_dir: str,
    runs_dir: str,
    adapter: GeminiAdapter,
    max_turns: int,
    max_remediation: int,
) -> dict:
    """Run agent evaluation on a single task. Returns result dict."""
    print(f"\n{'='*60}")
    print(f"  TASK: {task_name}")
    print(f"  MODEL: {adapter.model}")
    print(f"{'='*60}")

    start_time = time.time()

    # Stage workspace
    run_id, run_dir, task_dir = setup_run(task_name, tasks_dir, runs_dir)
    print(f"  Run ID: {run_id}")
    print(f"  Run dir: {run_dir}")

    # Run orchestrator
    orchestrator = TaskOrchestrator(
        task_dir=task_dir,
        run_dir=run_dir,
        adapter=adapter,
        max_turns_per_phase=max_turns,
        max_remediation_loops=max_remediation,
    )

    orch_result = orchestrator.run()
    elapsed = time.time() - start_time

    # Run grader
    score = grade_run(task_name, task_dir, run_dir)

    # Write meta.json
    usage = adapter.get_usage()
    meta = {
        "task_id": task_name,
        "run_id": run_id,
        "model": adapter.model,
        "agent_verdict": orch_result.verdict,
        "grader_verdict": "pass" if score.get("pass") else "fail",
        "total_turns": orch_result.total_turns,
        "remediation_loops": orch_result.remediation_loops,
        "elapsed_sec": round(elapsed, 1),
        "token_usage": usage,
        "score": score,
    }
    meta_path = os.path.join(run_dir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # Print summary
    print(f"\n  --- Results for {task_name} ---")
    print(f"  Agent verdict: {orch_result.verdict}")
    print(f"  Grader verdict: {'PASS' if score.get('pass') else 'FAIL'}")
    print(f"  Total turns: {orch_result.total_turns}")
    print(f"  Remediation loops: {orch_result.remediation_loops}")
    print(f"  Elapsed: {elapsed:.1f}s")
    print(f"  Tokens: {usage['total_tokens']} (in={usage['input_tokens']}, out={usage['output_tokens']})")
    if score.get("failure_modes"):
        print(f"  Failure modes: {score['failure_modes']}")
    if score.get("secondary", {}).get("partial_score") is not None:
        print(f"  Partial score: {score['secondary']['partial_score']}")

    return meta


def main() -> None:
    ap = argparse.ArgumentParser(description="TeamBench agent driver")
    ap.add_argument("--task", required=True, help="Task name (e.g., S1_hidden_spec) or 'all'")
    ap.add_argument("--model", default="gemini-2.5-flash", help="Gemini model name")
    ap.add_argument("--tasks-dir", default="tasks", help="Tasks directory")
    ap.add_argument("--runs-dir", default="shared/runs", help="Runs output directory")
    ap.add_argument("--max-turns", type=int, default=20, help="Max turns per phase")
    ap.add_argument("--max-remediation", type=int, default=2, help="Max remediation loops")
    ap.add_argument("--temperature", type=float, default=0.2, help="Model temperature")
    args = ap.parse_args()

    tasks_dir = os.path.abspath(args.tasks_dir)
    runs_dir = os.path.abspath(args.runs_dir)

    # Load API key and create adapter
    api_key = load_api_key()
    adapter = GeminiAdapter(
        api_key=api_key,
        model=args.model,
        temperature=args.temperature,
    )

    # Determine tasks to run
    if args.task.lower() == "all":
        task_names = discover_tasks(tasks_dir)
    else:
        task_names = [args.task]

    print(f"TeamBench Agent Driver")
    print(f"Model: {args.model}")
    print(f"Tasks: {task_names}")

    all_results = []
    for task_name in task_names:
        try:
            result = run_single_task(
                task_name=task_name,
                tasks_dir=tasks_dir,
                runs_dir=runs_dir,
                adapter=adapter,
                max_turns=args.max_turns,
                max_remediation=args.max_remediation,
            )
            all_results.append(result)
        except Exception as e:
            print(f"\n  ERROR running {task_name}: {e}")
            all_results.append({"task_id": task_name, "error": str(e)})

    # Print final summary
    if len(all_results) > 1:
        print(f"\n{'='*60}")
        print(f"  BATCH SUMMARY")
        print(f"{'='*60}")
        passed = sum(1 for r in all_results if r.get("grader_verdict") == "pass")
        total = len(all_results)
        print(f"  Passed: {passed}/{total} ({passed/max(1,total):.0%})")
        for r in all_results:
            status = r.get("grader_verdict", "error").upper()
            print(f"    {r['task_id']}: {status}")

        # Write batch results
        batch_path = os.path.join(runs_dir, "agent_batch_results.json")
        with open(batch_path, "w", encoding="utf-8") as f:
            json.dump({"results": all_results, "model": args.model}, f, indent=2)
        print(f"\n  Batch results: {batch_path}")


if __name__ == "__main__":
    main()
