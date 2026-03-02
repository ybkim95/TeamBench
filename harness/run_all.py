"""
TeamBench batch runner — run and grade all tasks sequentially.

Usage:
    python -m harness.run_all
    python -m harness.run_all --tasks S1_hidden_spec O1_service_health
    python -m harness.run_all --skip-docker   # Grade-only mode (no container launch)
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import shutil
import uuid
from datetime import datetime, timezone


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def discover_tasks(tasks_dir: str) -> list[str]:
    """Find all task folders that contain task.yaml."""
    tasks = []
    for entry in sorted(os.listdir(tasks_dir)):
        task_path = os.path.join(tasks_dir, entry)
        if os.path.isdir(task_path) and os.path.isfile(os.path.join(task_path, "task.yaml")):
            tasks.append(entry)
    return tasks


def setup_run(task_name: str, tasks_dir: str, runs_dir: str, seed: int = 0) -> tuple[str, str, str]:
    """Create run directory and stage workspace. Returns (run_id, run_dir, task_dir)."""
    task_dir = os.path.join(tasks_dir, task_name)
    run_id = f"{now_utc()}_{uuid.uuid4().hex[:8]}"
    run_dir = os.path.join(runs_dir, task_name, run_id)

    workspace = os.path.join(run_dir, "workspace")
    reports = os.path.join(run_dir, "reports")
    messages = os.path.join(run_dir, "messages")
    submission = os.path.join(run_dir, "submission")

    for d in [workspace, reports, messages, submission]:
        os.makedirs(d, exist_ok=True)

    # Try parameterized generator first, fall back to static workspace + setup.sh
    generated = False
    try:
        from generators.registry import has_generator, get_generator
        if has_generator(task_name):
            gen = get_generator(task_name)
            result = gen.generate(seed=seed)
            gen.write_to_disk(result, workspace_dir=workspace, reports_dir=reports)
            generated = True
    except ImportError:
        pass

    if not generated:
        # Stage static workspace snapshot
        seed_src = os.path.join(task_dir, "workspace")
        if os.path.isdir(seed_src):
            for item in os.listdir(seed_src):
                s = os.path.join(seed_src, item)
                d = os.path.join(workspace, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)

        # Run setup.sh with seed
        setup = os.path.join(task_dir, "setup.sh")
        if os.path.isfile(setup):
            import subprocess
            subprocess.run(
                ["bash", setup, workspace, reports, run_id, str(seed)],
                check=True, capture_output=True, text=True,
            )

    # Write run metadata
    meta = {"task_id": task_name, "run_id": run_id, "seed": seed}
    with open(os.path.join(run_dir, "run_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    return run_id, run_dir, task_dir


def grade_run(task_name: str, task_dir: str, run_dir: str) -> dict:
    """Grade a completed run. Returns score dict."""
    import subprocess

    workspace = os.path.abspath(os.path.join(run_dir, "workspace"))
    reports = os.path.abspath(os.path.join(run_dir, "reports"))
    submission = os.path.abspath(os.path.join(run_dir, "submission"))
    score_path = os.path.join(reports, "score.json")

    # Run grader — pass expected.json as $5 if it exists (seed-aware grading)
    # Note: attestation check is handled within each grader (not pre-filtered here)
    # so we always get partial credit and full diagnostics even when attestation is missing.
    # All paths must be absolute because graders use `cd "$WORKSPACE"`.
    grade_script = os.path.abspath(os.path.join(task_dir, "grade.sh"))
    task_dir_abs = os.path.abspath(task_dir)
    expected_path = os.path.join(reports, "expected.json")
    grade_args = ["bash", grade_script, workspace, reports, submission, task_dir_abs]
    if os.path.isfile(expected_path):
        grade_args.append(expected_path)

    # Inject the current Python interpreter's bin dir into PATH so grade.sh
    # picks up pip, python, mypy, ruff, pylint, pip-audit etc. from the venv.
    import sys as _sys
    grade_env = os.environ.copy()
    venv_bin = os.path.dirname(os.path.abspath(_sys.executable))
    grade_env["PATH"] = venv_bin + os.pathsep + grade_env.get("PATH", "")

    subprocess.run(grade_args, check=False, capture_output=True, text=True, env=grade_env)

    if os.path.isfile(score_path):
        try:
            return json.loads(pathlib.Path(score_path).read_text())
        except json.JSONDecodeError:
            pass  # fall through to grader_no_score

    return {
        "pass": False,
        "primary": {"success": 0},
        "secondary": {},
        "failure_modes": ["grader_no_score"],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="TeamBench batch runner")
    ap.add_argument("--tasks", nargs="*", default=None, help="Specific tasks to run (default: all)")
    ap.add_argument("--tasks_dir", default="tasks", help="Tasks directory")
    ap.add_argument("--runs_dir", default="shared/runs", help="Runs output directory")
    ap.add_argument("--output", default="shared/batch_results.json", help="Batch results output")
    ap.add_argument("--seeds", nargs="*", type=int, default=[0], help="Seeds to evaluate (default: [0])")
    args = ap.parse_args()

    tasks_dir = os.path.abspath(args.tasks_dir)

    if args.tasks:
        task_names = args.tasks
    else:
        task_names = discover_tasks(tasks_dir)

    print(f"TeamBench Batch Runner")
    print(f"Tasks: {len(task_names)}")
    print(f"=" * 60)

    results = []
    passed = 0
    failed = 0

    for task_name in task_names:
        for seed in args.seeds:
            seed_label = f" (seed={seed})" if len(args.seeds) > 1 else ""
            print(f"\n--- {task_name}{seed_label} ---")

            try:
                run_id, run_dir, task_dir = setup_run(task_name, tasks_dir, args.runs_dir, seed=seed)
                print(f"  Run ID: {run_id}")
                print(f"  Run dir: {run_dir}")

                # Note: In automated mode, agent driver would interact here.
                # For batch validation, we grade the initial (buggy) state.
                score = grade_run(task_name, task_dir, run_dir)

                result = {
                    "task_id": task_name,
                    "seed": seed,
                    "run_id": run_id,
                    "run_dir": run_dir,
                    **score,
                }
                results.append(result)

                status = "PASS" if score.get("pass") else "FAIL"
                if score.get("pass"):
                    passed += 1
                else:
                    failed += 1
                print(f"  Result: {status}")
                if score.get("failure_modes"):
                    print(f"  Failures: {score['failure_modes']}")

            except Exception as e:
                print(f"  ERROR: {e}")
                results.append({
                    "task_id": task_name,
                    "seed": seed,
                    "pass": False,
                    "error": str(e),
                })
                failed += 1

    print(f"\n{'=' * 60}")
    print(f"TOTAL: {len(results)} tasks | {passed} passed | {failed} failed")
    print(f"Success rate: {passed / max(1, len(results)):.1%}")

    # Write batch results
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    batch = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "success_rate": round(passed / max(1, len(results)), 4),
        "results": results,
    }
    with open(args.output, "w") as f:
        json.dump(batch, f, indent=2)

    print(f"\nResults written to: {args.output}")


if __name__ == "__main__":
    main()
