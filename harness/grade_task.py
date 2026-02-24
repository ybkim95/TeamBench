"""
TeamBench task grader.

Usage:
    python -m harness.grade_task --task S1_hidden_spec --run_dir shared/runs/<run_id>
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import subprocess

from harness.utils import dir_sha256


def main() -> None:
    ap = argparse.ArgumentParser(description="TeamBench task grader")
    ap.add_argument("--task", required=True, help="Task folder name")
    ap.add_argument("--run_dir", required=True, help="Run directory path")
    ap.add_argument("--seed", type=int, default=0, help="Seed (for parameterized grading)")
    args = ap.parse_args()

    task_dir = os.path.abspath(os.path.join("tasks", args.task))
    run_dir = os.path.abspath(args.run_dir)

    workspace = os.path.join(run_dir, "workspace")
    reports = os.path.join(run_dir, "reports")
    submission = os.path.join(run_dir, "submission")
    score_path = os.path.join(reports, "score.json")

    # Hard rule: attestation.json must exist
    att_path = os.path.join(submission, "attestation.json")
    if not os.path.isfile(att_path):
        print("FAIL: missing verifier attestation.json")
        out = {
            "pass": False,
            "primary": {"success": 0},
            "secondary": {},
            "failure_modes": ["missing_attestation"],
        }
        pathlib.Path(score_path).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(score_path).write_text(json.dumps(out, indent=2))
        print(json.dumps(out, indent=2))
        return

    # Attach integrity hashes to attestation for audit
    att = json.loads(open(att_path, "r", encoding="utf-8").read())
    att["workspace_sha256"] = dir_sha256(workspace)
    att["reports_sha256"] = dir_sha256(reports)
    with open(att_path, "w", encoding="utf-8") as f:
        json.dump(att, f, indent=2, ensure_ascii=False)

    # Run task-specific grader
    grade_script = os.path.join(task_dir, "grade.sh")
    if not os.path.isfile(grade_script):
        raise FileNotFoundError(f"Missing grade.sh in {task_dir}")

    # Pass expected.json path as $5 if it exists (seed-aware grading)
    expected_path = os.path.join(reports, "expected.json")
    grade_args = ["bash", grade_script, workspace, reports, submission, task_dir]
    if os.path.isfile(expected_path):
        grade_args.append(expected_path)

    res = subprocess.run(
        grade_args,
        check=False,
        text=True,
        capture_output=True,
    )

    if res.returncode != 0:
        print(f"Grader stderr:\n{res.stderr}")

    if not os.path.isfile(score_path):
        out = {
            "pass": False,
            "primary": {"success": 0},
            "secondary": {},
            "failure_modes": ["grader_no_score_json"],
            "grader_stdout": res.stdout,
            "grader_stderr": res.stderr,
        }
        pathlib.Path(score_path).write_text(json.dumps(out, indent=2))
        print(json.dumps(out, indent=2))
        return

    score = json.loads(open(score_path, "r", encoding="utf-8").read())
    print(json.dumps(score, indent=2))

    if score.get("pass"):
        print("\nRESULT: PASS")
    else:
        print(f"\nRESULT: FAIL ({score.get('failure_modes', [])})")


if __name__ == "__main__":
    main()
