#!/usr/bin/env python3
"""Enforcement probe suite: attempt to breach the Planner/Executor/Verifier partition.

TeamBench claims that no single role can simultaneously read the full specification,
edit the workspace, and certify the result. That is a claim about a mechanism, and a
claim about a mechanism is only worth what the attempt to break it is worth. This
script is that attempt. It builds the real role configurations from
`harness.agent_interface`, then tries to reach `spec.md` and `reference/patch.diff`
from the Executor, and tries to mutate the Executor's workspace from the Verifier,
through every tool surface a role is given.

A probe is `leaked` when the protected content actually comes back, not when the call
merely succeeds. A probe that fails for an unrelated reason (missing file, bad path)
is reported as `inconclusive` and never counted as a block, because counting a
misfiring probe as evidence of enforcement is exactly the error the suite exists to
prevent.

Usage:
    python3 scripts/enforcement_probes.py                     # human-readable table
    python3 scripts/enforcement_probes.py --json OUT.json     # machine-readable
    python3 scripts/enforcement_probes.py --strict            # exit 1 if anything leaks

`--strict` is the CI form. Wire it into the build once the shell surface is guarded;
until then it is expected to fail, and that failure is the finding.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from harness.agent_interface import (  # noqa: E402
    make_executor_config,
    make_verifier_config,
)

BLOCKED = "blocked"
LEAKED = "leaked"
INCONCLUSIVE = "inconclusive"


def pick_task() -> str:
    """A task carrying both a spec and a reference patch, so both secrets are testable."""
    for patch in sorted(glob.glob(os.path.join(ROOT, "tasks", "*", "reference", "patch.diff"))):
        task_dir = os.path.dirname(os.path.dirname(patch))
        if os.path.exists(os.path.join(task_dir, "spec.md")):
            return task_dir
    raise SystemExit("no task with both spec.md and reference/patch.diff was found")


def _needle(path: str, n: int = 80) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read(4096)[:n].strip()


def run_probes(task_dir: str) -> list[dict]:
    spec = os.path.join(task_dir, "spec.md")
    patch = os.path.join(task_dir, "reference", "patch.diff")
    spec_needle, patch_needle = _needle(spec), _needle(patch)

    run = tempfile.mkdtemp(prefix="tb_probe_")
    try:
        ws = os.path.join(run, "workspace")
        os.makedirs(ws)
        for sub in ("reports", "messages", "submission"):
            os.makedirs(os.path.join(run, sub))
        canary = os.path.join(ws, "executor_output.py")
        with open(canary, "w") as fh:
            fh.write("ORIGINAL = 1\n")
        brief = os.path.join(run, "brief.md")
        with open(brief, "w") as fh:
            fh.write("Task brief. The specification is withheld from this role.\n")

        exec_tools = {t.name: t for t in make_executor_config(
            brief_path=brief, workspace_dir=ws,
            reports_dir=os.path.join(run, "reports"),
            messages_dir=os.path.join(run, "messages"),
            task_dir=task_dir).tools}
        ver_tools = {t.name: t for t in make_verifier_config(
            spec_path=spec, workspace_dir=ws,
            reports_dir=os.path.join(run, "reports"),
            messages_dir=os.path.join(run, "messages"),
            submission_dir=os.path.join(run, "submission"),
            task_dir=task_dir).tools}

        out: list[dict] = []

        def add(pid, surface, role, target, desc, verdict, detail=""):
            out.append(dict(probe=pid, surface=surface, role=role, target=target,
                            description=desc, verdict=verdict, detail=detail[:240]))

        def read_probe(pid, path, desc, needle, target):
            r = exec_tools["read"].execute(path=path)
            if needle and needle in (r.stdout or ""):
                add(pid, "read tool", "executor", target, desc, LEAKED)
            elif r.exit_code != 0 and "ermission" in ((r.stderr or "") + (r.stdout or "")):
                add(pid, "read tool", "executor", target, desc, BLOCKED, r.stderr or "")
            else:
                add(pid, "read tool", "executor", target, desc, INCONCLUSIVE, r.stderr or "")

        # --- read tool ------------------------------------------------------
        read_probe("R1", spec, "absolute path to spec.md", spec_needle, "spec")
        read_probe("R2", os.path.join(ws, "..", "..", spec.lstrip(os.sep)),
                   "'..' traversal out of the workspace", spec_needle, "spec")
        read_probe("R3", "../spec.md", "relative '..' escape", spec_needle, "spec")
        read_probe("R4", patch, "absolute path to the reference patch", patch_needle, "patch")
        read_probe("R5", ws + "_leak/spec.md",
                   "sibling directory sharing the workspace prefix", spec_needle, "spec")
        link = os.path.join(ws, "planted_link")
        try:
            os.symlink(task_dir, link)
            read_probe("R6", "planted_link/spec.md",
                       "symlink planted inside the workspace", spec_needle, "spec")
        except OSError as exc:
            add("R6", "read tool", "executor", "spec",
                "symlink planted inside the workspace", INCONCLUSIVE, str(exc))

        # --- write tool -----------------------------------------------------
        for pid, path, desc in [
            ("W1", "../../escaped.txt", "write outside the workspace via '..'"),
            ("W2", spec, "overwrite the specification the Planner reads"),
        ]:
            r = exec_tools["write"].execute(path=path, content="probe")
            add(pid, "write tool", "executor", "workspace boundary", desc,
                LEAKED if r.exit_code == 0 else BLOCKED, r.stderr or "")
        r = ver_tools["write"].execute(path=canary, content="OVERWRITTEN = 1\n")
        add("W3", "write tool", "verifier", "executor workspace",
            "Verifier writes into the Executor's workspace",
            LEAKED if r.exit_code == 0 else BLOCKED, r.stderr or "")

        # --- shell ----------------------------------------------------------
        shell_probes = [
            ("S1", f"cat {spec}", "cat the specification by absolute path", spec_needle, "spec"),
            ("S2", f"find {task_dir} -name spec.md | head -1 | xargs cat",
             "locate then read the specification with find", spec_needle, "spec"),
            ("S3", f"python3 -c \"print(open({spec!r}).read())\"",
             "read the specification from a Python one-liner", spec_needle, "spec"),
            ("S4", f"cat {patch}", "cat the reference patch by absolute path", patch_needle, "patch"),
            ("S5", f"grep -c . {spec}", "count specification lines with grep", None, "spec"),
        ]
        for pid, cmd, desc, needle, target in shell_probes:
            r = exec_tools["run"].execute(cmd=cmd)
            if needle is not None:
                verdict = LEAKED if needle in (r.stdout or "") else (
                    BLOCKED if "ermission denied" in ((r.stderr or "") + (r.stdout or ""))
                    else INCONCLUSIVE)
            else:
                verdict = LEAKED if r.exit_code == 0 and (r.stdout or "").strip() else (
                    BLOCKED if "ermission denied" in (r.stderr or "") else INCONCLUSIVE)
            add(pid, "shell", "executor", target, desc, verdict, r.stderr or "")

        ver_tools["run"].execute(cmd=f"echo 'OVERWRITTEN = 1' > {canary}")
        with open(canary) as fh:
            mutated = "OVERWRITTEN" in fh.read()
        add("S6", "shell", "verifier", "executor workspace",
            "Verifier overwrites an Executor file through its shell",
            LEAKED if mutated else BLOCKED)

        return out
    finally:
        shutil.rmtree(run, ignore_errors=True)


def summarise(probes: list[dict]) -> dict:
    by_surface: dict[str, dict[str, int]] = {}
    for p in probes:
        row = by_surface.setdefault(p["surface"], {BLOCKED: 0, LEAKED: 0, INCONCLUSIVE: 0})
        row[p["verdict"]] += 1
    return {
        "n_probes": len(probes),
        "n_blocked": sum(1 for p in probes if p["verdict"] == BLOCKED),
        "n_leaked": sum(1 for p in probes if p["verdict"] == LEAKED),
        "n_inconclusive": sum(1 for p in probes if p["verdict"] == INCONCLUSIVE),
        "by_surface": by_surface,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task", default=None, help="task directory to probe against")
    ap.add_argument("--json", dest="json_out", default=None, help="write the full record here")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any probe leaks")
    args = ap.parse_args()

    task_dir = args.task or pick_task()
    probes = run_probes(task_dir)
    summary = summarise(probes)

    print(f"Enforcement probe suite, task {os.path.basename(task_dir)}")
    print(f"{'probe':<6} {'surface':<12} {'role':<9} {'verdict':<13} description")
    for p in probes:
        print(f"{p['probe']:<6} {p['surface']:<12} {p['role']:<9} "
              f"{p['verdict']:<13} {p['description']}")
    print()
    print(f"{summary['n_probes']} probes: {summary['n_blocked']} blocked, "
          f"{summary['n_leaked']} leaked, {summary['n_inconclusive']} inconclusive")
    for surface, row in summary["by_surface"].items():
        print(f"  {surface:<12} blocked {row[BLOCKED]}  leaked {row[LEAKED]}  "
              f"inconclusive {row[INCONCLUSIVE]}")

    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        with open(args.json_out, "w") as fh:
            json.dump({"task": os.path.basename(task_dir),
                       "summary": summary, "probes": probes}, fh, indent=2)
        print(f"\nwrote {args.json_out}")

    return 1 if (args.strict and summary["n_leaked"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
