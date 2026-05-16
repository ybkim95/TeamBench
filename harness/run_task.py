"""
TeamBench task runner.

Usage:
    python -m harness.run_task --task S1_hidden_spec
    python -m harness.run_task --task O1_service_health --runs_dir shared/runs
"""
from __future__ import annotations
import argparse
import os
import shutil
import uuid

from harness.utils import now_utc, sh


def main() -> None:
    ap = argparse.ArgumentParser(description="TeamBench task runner")
    ap.add_argument("--task", required=True, help="Task folder name, e.g. S1_hidden_spec")
    ap.add_argument("--runs_dir", default="shared/runs", help="Base directory for run artifacts")
    ap.add_argument("--seed", type=int, default=0, help="Seed for parameterized task generation")
    args = ap.parse_args()

    task_dir = os.path.abspath(os.path.join("tasks", args.task))
    assert os.path.isdir(task_dir), f"Missing task dir: {task_dir}"

    run_id = f"{now_utc()}_{uuid.uuid4().hex[:8]}"
    run_dir = os.path.abspath(os.path.join(args.runs_dir, run_id))

    workspace = os.path.join(run_dir, "workspace")
    reports = os.path.join(run_dir, "reports")
    messages = os.path.join(run_dir, "messages")
    submission = os.path.join(run_dir, "submission")

    for d in [workspace, reports, messages, submission]:
        os.makedirs(d, exist_ok=True)

    # 1) Stage workspace snapshot
    seed_src = os.path.join(task_dir, "workspace")
    if os.path.isdir(seed_src):
        for item in os.listdir(seed_src):
            s = os.path.join(seed_src, item)
            d = os.path.join(workspace, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

    # 2) Run parameterized generator if available, otherwise setup.sh
    try:
        from generators.registry import has_generator, get_generator
        if has_generator(args.task):
            gen = get_generator(args.task)
            result = gen.generate(seed=args.seed)
            gen.write_to_disk(result, workspace_dir=workspace, reports_dir=reports)
            # Write seed-specific spec.md and brief.md to task_dir for Docker mount.
            # Ensure task_dir exists: on a fresh clone, a generator-driven task may
            # ship without a populated tasks/<TASK_ID>/ directory, so create it
            # on demand instead of failing with FileNotFoundError.
            os.makedirs(task_dir, exist_ok=True)
            with open(os.path.join(task_dir, "spec.md"), "w") as f:
                f.write(result.spec_md)
            with open(os.path.join(task_dir, "brief.md"), "w") as f:
                f.write(result.brief_md)
            print(f"  Generated parameterized instance (seed={args.seed})")
        else:
            setup = os.path.join(task_dir, "setup.sh")
            if os.path.isfile(setup):
                sh(["bash", setup, workspace, reports, run_id, str(args.seed)])
    except ImportError:
        setup = os.path.join(task_dir, "setup.sh")
        if os.path.isfile(setup):
            sh(["bash", setup, workspace, reports, run_id, str(args.seed)])

    # 3) Launch containers
    env = os.environ.copy()
    env["TASK_DIR"] = task_dir
    env["RUN_DIR"] = run_dir
    # Set CORPUS_DIR for Docker mount (falls back to .empty_corpus if no corpus/)
    corpus_dir = os.path.join(task_dir, "corpus")
    if os.path.isdir(corpus_dir):
        env["CORPUS_DIR"] = corpus_dir
    else:
        env["CORPUS_DIR"] = os.path.abspath(".empty_corpus")

    sh(["docker", "compose", "-f", "docker-compose.yml", "up", "-d", "--build"], env=env)

    print()
    print("=" * 60)
    print(f"  RUN READY")
    print(f"  run_id:   {run_id}")
    print(f"  task:     {args.task}")
    print(f"  run_dir:  {run_dir}")
    print("=" * 60)
    print()
    print("Interact via:")
    print("  docker exec -it teambench_planner bash")
    print("  docker exec -it teambench_executor bash")
    print("  docker exec -it teambench_verifier bash")
    print()
    print("When done, grade with:")
    print(f"  python -m harness.grade_task --task {args.task} --run_dir {run_dir}")
    print()
    print("Tear down with:")
    print("  docker compose down")


if __name__ == "__main__":
    main()
