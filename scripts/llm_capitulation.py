#!/usr/bin/env python3
"""Does the LLM Verifier capitulate the way the human Verifier does?

In the human study, 8 of 12 false accepts followed one path: the Verifier issued
a correct `fail`, the Executor was sent back, the deterministic grader score did
not move, and the Verifier then approved the same artifact. We called that
capitulation, and it is computed from the verdict sequence rather than read out
of the notes.

The Full-Team orchestrator runs the same loop for agents: verification, then up
to two remediation rounds, with a fresh Verifier invocation each time. This
script reconstructs the agent-side verdict sequence and applies the identical
criterion, so the human and agent numbers are produced by the same rule.

Method
------
Each run directory carries logs/verifier/attempt_N/turn_*.json. The attestation
file itself is overwritten every attempt, so the per-attempt verdict is recovered
from the `write` tool call inside the turn logs. Workspace change between rounds
is detected from logs/../workspace_snapshots/pre_remediation_N when present, and
otherwise reported as unknown rather than assumed.

Emits one row per run with >= 2 verifier attempts.
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERDICT_RE = re.compile(r'"verdict"\s*:\s*"(pass|fail)"')
# Shell forms that can alter the workspace. Deliberately broad: a false
# "changed" only makes the capitulation count more conservative.
MUTATING_RE = re.compile(
    r"(>>?\s|\bsed\s+-i\b|\bmv\b|\bcp\b|\brm\b|\btouch\b|\bpatch\b|\btee\b|"
    r"\bmkdir\b|\bchmod\b|\bgit\s+(apply|checkout|restore)\b|open\([^)]*['\"]w)")


def verdict_from_attempt(attempt_dir: str):
    """Recover the verdict this attempt filed, from its write tool call."""
    turns = sorted(glob.glob(os.path.join(attempt_dir, "turn_*.json")))
    verdict = None
    for tp in turns:
        try:
            t = json.load(open(tp, encoding="utf-8", errors="replace"))
        except Exception:
            continue
        for call in (t.get("tool_calls") or []):
            if call.get("name") != "write":
                continue
            args = call.get("args") or {}
            if "attestation" not in str(args.get("path", "")):
                continue
            m = VERDICT_RE.search(str(args.get("content", "")))
            if m:
                verdict = m.group(1)          # last write in the attempt wins
    return verdict, len(turns)


def dir_hash(path: str) -> str | None:
    if not os.path.isdir(path):
        return None
    h = hashlib.sha256()
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for fn in sorted(files):
            p = os.path.join(root, fn)
            h.update(os.path.relpath(p, path).encode())
            try:
                with open(p, "rb") as f:
                    h.update(f.read())
            except OSError:
                pass
    return h.hexdigest()


def analyse_run(run_dir: str):
    vdir = os.path.join(run_dir, "logs", "verifier")
    attempts = sorted(glob.glob(os.path.join(vdir, "attempt_*")),
                      key=lambda p: int(p.rsplit("_", 1)[-1]))
    if len(attempts) < 2:
        return None
    seq = []
    for a in attempts:
        v, n = verdict_from_attempt(a)
        seq.append({"attempt": int(a.rsplit("_", 1)[-1]), "verdict": v, "turns": n})

    # Did the Executor change anything between the fail and the next verdict?
    #
    # Older runs predate workspace_snapshots/, so the primary signal is the
    # remediation phase's own tool log: if the Executor issued no write call and
    # no mutating shell command, the artifact the Verifier re-approved is
    # byte-identical to the one it had just rejected. Snapshots are used when
    # present as a stronger check.
    snaps = sorted(glob.glob(os.path.join(run_dir, "workspace_snapshots", "pre_remediation_*")),
                   key=lambda p: int(p.rsplit("_", 1)[-1]))
    final_ws = os.path.join(run_dir, "workspace")
    changed = None
    evidence = None
    if snaps and os.path.isdir(final_ws):
        changed = dir_hash(snaps[-1]) != dir_hash(final_ws)
        evidence = "workspace_snapshot"
    else:
        rem = sorted(glob.glob(os.path.join(run_dir, "logs", "executor", "remediation_*")),
                     key=lambda p: int(p.rsplit("_", 1)[-1]))
        if rem:
            n_write, n_mutate, n_turns = 0, 0, 0
            for rd in rem:
                for tp in sorted(glob.glob(os.path.join(rd, "turn_*.json"))):
                    n_turns += 1
                    try:
                        t = json.load(open(tp, encoding="utf-8", errors="replace"))
                    except Exception:
                        continue
                    for call in (t.get("tool_calls") or []):
                        nm = call.get("name")
                        args = call.get("args") or {}
                        if nm == "write":
                            n_write += 1
                        elif nm == "run" and MUTATING_RE.search(str(args.get("cmd", ""))):
                            n_mutate += 1
            changed = (n_write + n_mutate) > 0
            evidence = f"remediation_tool_log(writes={n_write},mutating_cmds={n_mutate},turns={n_turns})"

    verdicts = [s["verdict"] for s in seq]
    flip = any(verdicts[i] == "fail" and verdicts[i + 1] == "pass"
               for i in range(len(verdicts) - 1))
    return {
        "run_dir": run_dir,
        "task": os.path.basename(os.path.dirname(run_dir)),
        "n_attempts": len(seq),
        "verdicts": verdicts,
        "fail_then_pass": flip,
        "workspace_changed_after_last_fail": changed,
        "change_evidence": evidence,
        "capitulation": bool(flip and changed is False),
        "sequence": seq,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+",
                    default=["shared/ablation_runs", "shared/gemma4_26b_api_campaign/runs",
                             "shared/role_ablation/runs"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="shared/paper/quality/llm_capitulation.json")
    a = ap.parse_args()

    runs = []
    for root in a.roots:
        root = os.path.join(REPO, root)
        if not os.path.isdir(root):
            continue
        # a run dir is any directory that contains logs/verifier
        for vdir in glob.glob(os.path.join(root, "*", "*", "logs", "verifier")):
            runs.append(os.path.dirname(os.path.dirname(vdir)))
    runs = sorted(set(runs))
    if a.limit:
        runs = runs[: a.limit]
    print(f"run directories with a verifier log: {len(runs)}", flush=True)

    out = []
    for i, r in enumerate(runs, 1):
        try:
            res = analyse_run(r)
        except Exception:
            res = None
        if res:
            out.append(res)
        if i % 200 == 0:
            print(f"  scanned {i}/{len(runs)}, multi-attempt so far {len(out)}", flush=True)

    os.makedirs(os.path.dirname(os.path.join(REPO, a.out)), exist_ok=True)
    json.dump(out, open(os.path.join(REPO, a.out), "w"), indent=1)

    flips = [r for r in out if r["fail_then_pass"]]
    known = [r for r in flips if r["workspace_changed_after_last_fail"] is not None]
    cap = [r for r in known if r["capitulation"]]
    print(f"\nruns with >= 2 verifier attempts       : {len(out)}")
    print(f"  verdict went fail -> pass            : {len(flips)}")
    print(f"  of those, workspace change resolvable: {len(known)}")
    print(f"  CAPITULATION (flip, workspace same)  : {len(cap)}"
          + (f" = {100*len(cap)/len(known):.0f}% of resolvable flips" if known else ""))
    seqs = collections.Counter(tuple(r["verdicts"]) for r in out)
    print("\n  most common verdict sequences:")
    for s, n in seqs.most_common(8):
        print(f"    {list(s)}  {n}")
    print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
