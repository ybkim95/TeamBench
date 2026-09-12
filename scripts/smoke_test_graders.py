#!/usr/bin/env python3
"""Smoke-test every grader in the 100-task leaderboard set.

For each task:
  1. setup_run() to stage a fresh workspace
  2. grade_run() without any agent submission
  3. Verify reports/score.json is written with valid pass/partial

Prints a clear table of results. Exit 1 if any task fails the smoke test.
"""
import json, os, sys, tempfile, shutil, traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
os.chdir(Path(__file__).parent.parent.resolve())

from harness.run_all import setup_run, grade_run

tasks_json = json.load(open("leaderboard/data/leaderboard_100_tasks.json"))
task_ids = [t["task_id"] for t in tasks_json["tasks"]]

print(f"Smoke-testing {len(task_ids)} graders...")
print(f"{'task_id':<45} {'score.json':<12} {'partial':>7} {'pass':<6} {'notes'}")
print("-" * 90)

with tempfile.TemporaryDirectory() as tmp:
    runs_dir = os.path.join(tmp, "runs")
    passed = failed = broken = 0
    for tid in task_ids:
        try:
            run_id, run_dir, task_dir = setup_run(tid, "tasks", runs_dir, seed=0)
            score = grade_run(tid, task_dir, run_dir)
            score_path = os.path.join(run_dir, "reports", "score.json")
            has_score = os.path.isfile(score_path)
            partial = score.get("secondary", {}).get("partial_score", None)
            p = score.get("pass", False)
            fm = score.get("failure_modes", [])
            status = "OK"
            if not has_score:
                status = "BROKEN (no score.json)"
                broken += 1
            elif "grader_no_score" in fm:
                status = "BROKEN (grader_no_score)"
                broken += 1
            else:
                passed += 1
            partial_str = f"{partial:.2f}" if partial is not None else "-"
            print(f"{tid:<45} {str(has_score):<12} {partial_str:>7} {str(p):<6} {status}")
        except Exception as e:
            failed += 1
            print(f"{tid:<45} EXCEPTION: {type(e).__name__}: {str(e)[:60]}")

print("-" * 90)
print(f"Summary: {passed} ok, {broken} broken, {failed} exception")
sys.exit(0 if broken == 0 and failed == 0 else 1)
