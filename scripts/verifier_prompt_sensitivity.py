#!/usr/bin/env python3
"""Verifier prompt sensitivity: hold the artifact fixed, vary only the instruction.

Why
---
The paper's headline verifier number (about 50% of grader-failing submissions
approved) was measured under the Full-Team verifier turn prompt in
harness/orchestrator.py, which instructs the model to

    "Set verdict='pass' if the CORE requirements are met, even if minor
     stylistic issues remain. Only set verdict='fail' for clear, objective
     violations of explicit spec requirements."

That is a leniency instruction, and a reviewer will say the finding is an
artifact of it. This experiment answers that directly.

Design
------
The 2,025 role-mixing runs left their workspaces on disk, each with a known
deterministic grader outcome. We re-verify those FIXED artifacts under three
verdict instructions and three models. Nothing about the submitted work changes
between arms, so any difference in the false-accept rate is attributable to the
instruction alone. This is a much tighter design than re-running whole teams.

  arm LENIENT  the prompt that produced the published number
  arm NEUTRAL  a plain "check every requirement" instruction, no verdict steer
  arm STRICT   an auditor framing: fail is the default, pass requires positive
               evidence the verifier obtained itself

Output: shared/paper/quality/verifier_prompt_sensitivity.jsonl (one row per
(workspace, prompt, model)) plus a summary JSON.

Usage:
  python scripts/verifier_prompt_sensitivity.py --n-fail 40 --n-pass 15 \
      --models gemini-3-flash-preview claude-haiku-4-5-20251001 gpt-5.4-mini
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

OUT_DIR = os.path.join(REPO, "shared", "paper", "quality")
PER_RUN = os.path.join(REPO, "shared", "role_ablation", "results", "per_run.jsonl")

# The three verdict instructions. Everything else in the verifier prompt is
# identical across arms, so the arms differ only in how the verdict is steered.
PROMPTS = {
    "lenient": (
        "5. IMPORTANT: Set verdict='pass' if the CORE requirements are met, even if\n"
        "   minor stylistic issues remain. Only set verdict='fail' for clear, objective\n"
        "   violations of explicit spec requirements.\n"
    ),
    "neutral": (
        "5. Check each requirement in the specification against the workspace.\n"
        "   Set verdict='pass' if the requirements are satisfied, otherwise 'fail'.\n"
    ),
    "strict": (
        "5. You are an auditor. The default verdict is 'fail'. Set verdict='pass' only\n"
        "   if you have positively verified EVERY requirement using evidence you\n"
        "   obtained yourself in this session. A requirement you could not verify\n"
        "   counts as not satisfied.\n"
    ),
}


def build_prompt(task_id: str, spec_text: str, verdict_clause: str) -> str:
    return (
        f"You are the Verifier for task: {task_id}\n\n"
        f"## Full Specification\n{spec_text}\n\n"
        f"## Instructions\n"
        f"1. Read the specification carefully.\n"
        f"2. Check the workspace files to verify all requirements are met.\n"
        f"   Use read(path='app/main.py') etc. with relative paths to workspace.\n"
        f"3. For EACH requirement, verify compliance.\n"
        f"4. Write attestation.json. The content MUST be valid JSON, e.g.\n"
        f"   write(path='attestation.json', content='{{\"task_id\":\"{task_id}\","
        f"\"verdict\":\"pass\",\"checklist\":[]}}')\n"
        f"{verdict_clause}"
        f"6. Output DONE when finished."
    )


def load_pool():
    runs = {}
    with open(PER_RUN) as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            runs[(r.get("config"), r.get("task_id"), r.get("seed"))] = r
    alive = [r for r in runs.values()
             if r.get("run_dir") and os.path.isdir(os.path.join(r["run_dir"], "workspace"))]
    return alive


def sample(alive, n_fail, n_pass, seed=0):
    """Stratify the grader-FAIL pool across the partial-score range so the arms
    are not decided by a handful of near-misses."""
    rng = random.Random(seed)
    fails = [r for r in alive if not r.get("pass")]
    passes = [r for r in alive if r.get("pass")]
    bins = {"lo": [], "mid": [], "hi": []}
    for r in fails:
        s = r.get("partial_score") or 0.0
        bins["lo" if s < 0.34 else "mid" if s < 0.67 else "hi"].append(r)
    per = max(1, n_fail // 3)
    picked = []
    for b in bins.values():
        rng.shuffle(b)
        picked += b[:per]
    rng.shuffle(passes)
    return picked[:n_fail], passes[:n_pass]


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


def verify_once(run, prompt_name, adapter, max_turns=20):
    """Re-verify one fixed artifact under one verdict instruction."""
    from harness.agent_interface import make_verifier_config
    from harness.agent_loop import AgentLoop, TurnBudget

    task_id = run["task_id"]
    spec_p, task_dir = resolve_spec(task_id, run.get("seed"))
    if not spec_p:
        return {"error": "no_spec"}
    spec_text = open(spec_p, encoding="utf-8", errors="replace").read()

    tmp = tempfile.mkdtemp(prefix="vps_")
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
            task_dir=task_dir,
        )
        loop = AgentLoop(role_config=cfg, adapter=adapter,
                         messages_dir=os.path.join(tmp, "messages"),
                         log_dir=os.path.join(tmp, "logs"),
                         max_turns=max_turns, budget=TurnBudget(max_turns))
        t0 = time.time()
        turns = loop.run(build_prompt(task_id, spec_text, PROMPTS[prompt_name]))

        def read_verdict():
            """Find the attestation wherever the verifier actually put it.

            The harness only ever looks at <submission>/attestation.json. But the
            write tool resolves 'submission/attestation.json' to a NESTED
            <submission>/submission/attestation.json, and a verifier that writes a
            relative workspace path lands elsewhere again. Those runs are recorded
            as "missing attestation" even though a verdict exists on disk, so we
            search instead of assuming one location, and report which one was used.
            """
            import re
            cands = []
            for root in (os.path.join(tmp, "submission"), os.path.join(tmp, "workspace"),
                         os.path.join(tmp, "reports")):
                for dirpath, _, files in os.walk(root):
                    for fn in files:
                        if fn == "attestation.json":
                            cands.append(os.path.join(dirpath, fn))
            canonical = os.path.join(tmp, "submission", "attestation.json")
            cands.sort(key=lambda p: (p != canonical, len(p)))
            for p in cands:
                raw = open(p, encoding="utf-8", errors="replace").read()
                try:
                    v = (json.loads(raw) or {}).get("verdict")
                except Exception:
                    m = re.search(r'"verdict"\s*:\s*"(pass|fail)"', raw)
                    v = m.group(1) if m else None
                if v in ("pass", "fail"):
                    return v, os.path.relpath(p, tmp)
            return None, None

        natural, nat_path = read_verdict()
        forced, forced_path = natural, nat_path
        n_forced = 0
        if natural is None:
            # The verifier often exhausts its budget exploring and never files an
            # attestation. That missingness is itself a finding, but if it differed
            # by arm it would confound the prompt comparison, so we also elicit a
            # verdict under a short forcing turn and report both. The forcing turn
            # repeats the arm's own verdict clause so the steer is preserved.
            force_loop = AgentLoop(
                role_config=cfg, adapter=adapter,
                messages_dir=os.path.join(tmp, "messages"),
                log_dir=os.path.join(tmp, "logs_forced"),
                max_turns=3, budget=TurnBudget(3))
            ft = force_loop.run(
                f"You have finished inspecting task {task_id}. Do not inspect further.\n"
                f"Write your verdict now and nothing else:\n"
                f"  write(path='attestation.json', content='{{\"task_id\":\"{task_id}\","
                f"\"verdict\":\"pass\",\"checklist\":[]}}')\n"
                f"{PROMPTS[prompt_name]}"
                f"Then output DONE.")
            n_forced = len(ft)
            forced, forced_path = read_verdict()

        return {"verdict": natural, "verdict_forced": forced,
                "was_forced": natural is None,
                "attestation_path": forced_path,
                "nonstandard_path": bool(forced_path) and forced_path != os.path.join("submission", "attestation.json"),
                "turns": len(turns), "forced_turns": n_forced,
                "seconds": round(time.time() - t0, 1)}
    except Exception as e:
        return {"error": str(e)[:160]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["gemini-3-flash-preview"])
    ap.add_argument("--n-fail", type=int, default=40)
    ap.add_argument("--n-pass", type=int, default=15)
    ap.add_argument("--prompts", nargs="+", default=list(PROMPTS))
    ap.add_argument("--out", default=os.path.join(OUT_DIR, "verifier_prompt_sensitivity.jsonl"))
    a = ap.parse_args()

    from harness.adapters import create_adapter

    os.makedirs(OUT_DIR, exist_ok=True)
    alive = load_pool()
    fails, passes = sample(alive, a.n_fail, a.n_pass)
    pool = [(r, False) for r in fails] + [(r, True) for r in passes]
    total = len(pool) * len(a.prompts) * len(a.models)
    print(f"[vps] artifacts: {len(fails)} grader-FAIL + {len(passes)} grader-PASS")
    print(f"[vps] arms: {a.prompts} x models {a.models} -> {total} verifier runs", flush=True)

    done = set()
    if os.path.isfile(a.out):
        for line in open(a.out):
            try:
                d = json.loads(line)
                done.add((d["model"], d["prompt"], d["run_dir"]))
            except Exception:
                pass
        print(f"[vps] resuming, {len(done)} already recorded", flush=True)

    i = 0
    with open(a.out, "a") as fh:
        for model in a.models:
            adapter = create_adapter(model=model, temperature=0.2)
            for prompt_name in a.prompts:
                for run, grader_pass in pool:
                    i += 1
                    key = (model, prompt_name, run["run_dir"])
                    if key in done:
                        continue
                    res = verify_once(run, prompt_name, adapter)
                    row = {"model": model, "prompt": prompt_name,
                           "task": run["task_id"], "config": run["config"],
                           "seed": run["seed"], "run_dir": run["run_dir"],
                           "grader_pass": grader_pass,
                           "grader_partial": run.get("partial_score"), **res}
                    fh.write(json.dumps(row) + "\n")
                    fh.flush()
                    if i % 20 == 0:
                        print(f"  [{i}/{total}] {model} {prompt_name} {run['task_id'][:24]} "
                              f"-> {res.get('verdict') or res.get('error')}", flush=True)
    print("[vps] done ->", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
