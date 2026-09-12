#!/usr/bin/env python3
"""Is Verifier abstention a model limitation or a harness permission?

Measured: LLM Verifiers file no verdict on 45.4% of runs, while human Verifiers
filed one in 28 of 28 sessions. The human platform did not let a session close
without a verdict; the agent harness does. So the gap may be structural rather
than a difference in diligence.

This tests that directly by varying only the termination rule, with the artifact
and the prompt held fixed:

  free     current harness behaviour. The loop ends on DONE or budget exhaustion,
           and a run that ends with no attestation is an abstention.
  blocked  the run cannot end without an attestation on disk. DONE is refused
           while the budget remains and the Verifier is re-prompted.

The headline is not the abstention rate, which `blocked` drives toward zero by
construction. It is what the coerced verdicts SAY. If forcing a decision mostly
produces `fail`, abstention was structural and the fix is to require a verdict.
If it mostly produces `pass`, then requiring a verdict converts silence into
false acceptance and the intuitive fix makes the control worse, not better.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

OUT_DIR = os.path.join(REPO, "shared", "paper", "quality")

NUDGES = [
    "You have not filed an attestation. You must record a verdict before you "
    "finish. Write it now with write(path='attestation.json', content='{\"task_id\":"
    "\"%s\",\"verdict\":\"pass\",\"checklist\":[]}') using pass or fail as appropriate.",
    "Reminder: this verification cannot be closed without a verdict on file. "
    "Stop inspecting and record pass or fail now.",
    "Final reminder. Record your verdict this turn. If you were unable to verify "
    "the requirements, that is a fail.",
]


def resolve_spec(task_id: str, seed=0):
    """Locate or materialise spec.md for a task id.

    Three layouts exist in this corpus and assuming one silently dropped 54 of
    180 runs in the first prompt-sensitivity sweep:
      1. tasks/<id>/spec.md
      2. tasks/<id>_seed<N>/spec.md      (per-seed siblings; RDS/ML families)
      3. no spec on disk at all          (generator-backed; the harness renders
                                          it at run time from gen_<id>.py)
    For case 3 the spec is regenerated at the run's own seed and cached under
    the scratch dir, so the Verifier sees exactly what it saw originally.
    """
    cands = [os.path.join(REPO, "tasks", task_id, "spec.md")]
    if seed is not None:
        cands.append(os.path.join(REPO, "tasks", f"{task_id}_seed{seed}", "spec.md"))
    cands.append(os.path.join(REPO, "tasks", f"{task_id}_seed0", "spec.md"))
    for p in cands:
        if os.path.isfile(p):
            return p, os.path.dirname(p)
    try:
        from generators.registry import get_generator
        gen = get_generator(task_id.lower())
        res = gen.generate(seed=int(seed or 0))
        spec = getattr(res, "spec_md", None)
        if spec:
            cache = os.path.join(REPO, "tasks", task_id)
            os.makedirs(cache, exist_ok=True)
            p = os.path.join(cache, "spec.generated.md")
            if not os.path.isfile(p):
                open(p, "w", encoding="utf-8").write(spec)
            return p, cache
    except Exception:
        pass
    return None, os.path.join(REPO, "tasks", task_id)


def run_arm(run, arm, prompt_name, adapter, budget=20):
    from harness.agent_interface import make_verifier_config
    from harness.agent_loop import AgentLoop, TurnBudget
    from verifier_prompt_sensitivity import build_prompt, PROMPTS

    task_id = run["task_id"]
    spec_p, task_dir = resolve_spec(task_id, run.get("seed"))
    if not spec_p:
        return {"error": "no_spec"}
    spec = open(spec_p, encoding="utf-8", errors="replace").read()

    tmp = tempfile.mkdtemp(prefix="fv_")
    try:
        ws = os.path.join(tmp, "workspace")
        shutil.copytree(os.path.join(run["run_dir"], "workspace"), ws)
        for d in ("reports", "messages", "submission"):
            os.makedirs(os.path.join(tmp, d), exist_ok=True)
        cfg = make_verifier_config(
            spec_path=spec_p, workspace_dir=ws,
            reports_dir=os.path.join(tmp, "reports"),
            messages_dir=os.path.join(tmp, "messages"),
            submission_dir=os.path.join(tmp, "submission"),
            task_dir=task_dir)

        def verdict_on_disk():
            import re
            for dirpath, _, files in os.walk(os.path.join(tmp, "submission")):
                for fn in files:
                    if fn != "attestation.json":
                        continue
                    raw = open(os.path.join(dirpath, fn), encoding="utf-8",
                               errors="replace").read()
                    try:
                        v = (json.loads(raw) or {}).get("verdict")
                    except Exception:
                        m = re.search(r'"verdict"\s*:\s*"(pass|fail)"', raw)
                        v = m.group(1) if m else None
                    if v in ("pass", "fail"):
                        return v
            return None

        # `blocked` must keep turns in hand to issue its reminder, so the main
        # inspection loop is capped below the shared budget in BOTH arms. Total
        # compute is therefore identical; only the right to stop differs.
        reserve = 5 if arm == "blocked" else 0
        shared = TurnBudget(budget)
        t0 = time.time()
        total_turns, nudges = 0, 0
        turns = AgentLoop(role_config=cfg, adapter=adapter,
                          messages_dir=os.path.join(tmp, "messages"),
                          log_dir=os.path.join(tmp, "logs_0"),
                          max_turns=budget - reserve, budget=shared
                          ).run(build_prompt(task_id, spec, PROMPTS[prompt_name]))
        total_turns += len(turns)

        if arm == "blocked":
            # Refuse to close without a verdict while budget remains. The same
            # shared TurnBudget is used throughout, so `blocked` never gets more
            # compute than `free`; it only spends it differently.
            while verdict_on_disk() is None and shared.remaining > 0 and nudges < len(NUDGES):
                msg = NUDGES[nudges]
                nudges += 1
                extra = AgentLoop(role_config=cfg, adapter=adapter,
                                  messages_dir=os.path.join(tmp, "messages"),
                                  log_dir=os.path.join(tmp, f"logs_n{nudges}"),
                                  max_turns=max(1, min(4, shared.remaining)),
                                  budget=shared
                                  ).run(msg % task_id if "%s" in msg else msg)
                total_turns += len(extra)

        return {"verdict": verdict_on_disk(), "turns": total_turns,
                "nudges": nudges, "budget_left": shared.remaining,
                "seconds": round(time.time() - t0, 1)}
    except Exception as e:
        return {"error": str(e)[:160]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemini-3-flash-preview")
    ap.add_argument("--prompt", default="neutral")
    ap.add_argument("--n-fail", type=int, default=40)
    ap.add_argument("--n-pass", type=int, default=10)
    ap.add_argument("--budget", type=int, default=20)
    ap.add_argument("--arms", nargs="+", default=["free", "blocked"])
    ap.add_argument("--out", default=os.path.join(OUT_DIR, "verifier_forced_verdict.jsonl"))
    a = ap.parse_args()

    from harness.adapters import create_adapter
    from verifier_prompt_sensitivity import load_pool, sample

    os.makedirs(OUT_DIR, exist_ok=True)
    alive = load_pool()
    fails, passes = sample(alive, a.n_fail, a.n_pass, seed=11)   # different draw
    pool = [(r, False) for r in fails] + [(r, True) for r in passes]
    print(f"[fv] artifacts {len(fails)} grader-FAIL + {len(passes)} grader-PASS, "
          f"arms {a.arms}, prompt={a.prompt} -> {len(pool)*len(a.arms)} runs", flush=True)

    done = set()
    if os.path.isfile(a.out):
        for line in open(a.out):
            try:
                d = json.loads(line)
                done.add((d["arm"], d["run_dir"]))
            except Exception:
                pass
        print(f"[fv] resuming, {len(done)} recorded", flush=True)

    adapter = create_adapter(model=a.model, temperature=0.2)
    i = 0
    with open(a.out, "a") as fh:
        for arm in a.arms:
            for run, gpass in pool:
                i += 1
                if (arm, run["run_dir"]) in done:
                    continue
                res = run_arm(run, arm, a.prompt, adapter, a.budget)
                fh.write(json.dumps({
                    "arm": arm, "model": a.model, "prompt": a.prompt,
                    "task": run["task_id"], "config": run["config"], "seed": run["seed"],
                    "run_dir": run["run_dir"], "grader_pass": gpass,
                    "grader_partial": run.get("partial_score"), **res}) + "\n")
                fh.flush()
                if i % 15 == 0:
                    print(f"  [{i}] {arm:7} {run['task_id'][:22]:22} -> "
                          f"{res.get('verdict') or res.get('error')}", flush=True)
    print("[fv] done ->", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
