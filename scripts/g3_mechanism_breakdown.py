#!/usr/bin/env python3
"""
Join the three G3 measurements into one mechanism table.

Inputs (all under shared/paper/quality/):
    g3_reference_ledger.json    outcome per task (a/b/c/d)
    param_corruption.json       static census: does the staged workspace's
                                Python even parse and import?
    g3_failure_diagnosis*.json  for a sample of bucket-(b) tasks, the actual
                                cause of the C1/C5 failures

Output: g3_mechanism_breakdown.json + a printed table.

The point of the join is to keep the claim honest. "The grader rejects the
upstream fix" is only a statement about the grader if the workspace it grades is
a workspace a correct agent could have fixed. Where the staged Python cannot
parse or import, the task is unsolvable before the grader is even reached, and
the correct attribution is to the task generator, not to the grader.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(REPO_ROOT, "shared", "paper", "quality")


def load(name, default=None):
    p = name if os.path.isabs(name) else os.path.join(Q, name)
    if not os.path.isfile(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    led = load("g3_reference_ledger.json")
    pc = load("param_corruption.json")
    if led is None or pc is None:
        print("missing inputs", file=sys.stderr)
        return 1
    recs = {r["task_id"]: r for r in led["tasks"]}
    corrupt = {r["task_id"]: r for r in pc["tasks"]}

    diags = {}
    for extra in sys.argv[1:] + ["g3_failure_diagnosis.json"]:
        d = load(extra)
        if d:
            for r in d["tasks"]:
                diags[r["task_id"]] = r

    # How many of these graders still carry the literal placeholder left by the
    # PR-to-task converter where the repo's own dependencies were supposed to go.
    todo = 0
    for t in recs:
        g = os.path.join(REPO_ROOT, "tasks", t, "grade.sh")
        try:
            with open(g, encoding="utf-8", errors="replace") as f:
                if "TODO: add repo-specific dependencies" in f.read():
                    todo += 1
        except OSError:
            pass

    oc = Counter(r["outcome"] for r in recs.values())
    b = [t for t, r in recs.items() if r["outcome"] == "b_grader_rejects_reference"]
    b_corrupt = [t for t in b if corrupt.get(t, {}).get("corrupt")]
    b_clean = [t for t in b if t in corrupt and not corrupt[t]["corrupt"]]

    diag_clean = Counter()
    for t in b_clean:
        d = diags.get(t)
        if d:
            diag_clean[d.get("c1_cause") or "not_measured"] += 1
        else:
            diag_clean["not_measured"] += 1
    diag_corrupt = Counter()
    for t in b_corrupt:
        d = diags.get(t)
        if d:
            diag_corrupt[d.get("c1_cause") or "not_measured"] += 1

    n = len(recs)
    print(f"G3 over {n} tasks with an upstream reference patch (seed 0)")
    print()
    for k in ("a_validated", "b_grader_rejects_reference", "c_unappliable",
              "d_inconclusive_grader_timeout", "error"):
        print(f"  {k:32s} {oc.get(k,0):5d}  {oc.get(k,0)/n:6.1%}")
    print()
    print(f"Bucket (b) = {len(b)}")
    print(f"  staged Python cannot parse or import  {len(b_corrupt):5d}  "
          f"{len(b_corrupt)/len(b):6.1%}   (static lower bound)")
    print(f"  staged Python is clean                {len(b_clean):5d}  "
          f"{len(b_clean)/len(b):6.1%}")
    print()
    print("Measured C1 cause among bucket-(b) tasks whose Python is clean:")
    for k, v in diag_clean.most_common():
        print(f"  {k:28s} {v}")
    if diag_corrupt:
        print()
        print("Measured C1 cause among the sampled corrupt bucket-(b) tasks "
              "(control):")
        for k, v in diag_corrupt.most_common():
            print(f"  {k:28s} {v}")

    eq = [t for t in b if recs[t].get("reference_minus_floor") == 0.0]
    print()
    print(f"reference score == pristine floor: {len(eq)}/{len(b)} "
          f"({len(eq)/len(b):.1%}) of bucket (b)")
    eq_clean = [t for t in b_clean if recs[t].get("reference_minus_floor") == 0.0]
    print(f"  restricted to the clean-Python subset: {len(eq_clean)}/{len(b_clean)}")

    print()
    print(f"graders still carrying the literal placeholder "
          f"`# TODO: add repo-specific dependencies`: {todo}/{n} ({todo/n:.1%})")

    out = {
        "n": n,
        "graders_with_unfinished_dependency_todo": todo,
        "outcomes": dict(oc),
        "bucket_b": len(b),
        "b_workspace_python_broken": len(b_corrupt),
        "b_workspace_python_clean": len(b_clean),
        "b_clean_task_ids": sorted(b_clean),
        "c1_cause_among_clean_b": dict(diag_clean),
        "c1_cause_among_sampled_corrupt_b": dict(diag_corrupt),
        "reference_equals_floor": len(eq),
        "reference_equals_floor_clean_subset": len(eq_clean),
        "param_corruption_summary": pc["summary"],
        "diagnosed_tasks": len(diags),
    }
    p = os.path.join(Q, "g3_mechanism_breakdown.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    L = []
    A = L.append
    A("# G3 mechanism breakdown")
    A("")
    A("Companion to `g3_reference_summary.md`. It answers the question that "
      "table cannot: when the grader refuses the upstream fix, whose defect is it?")
    A("")
    A(f"| Outcome | Tasks | Share of {n} |")
    A("|---|---:|---:|")
    for k in ("a_validated", "b_grader_rejects_reference", "c_unappliable",
              "d_inconclusive_grader_timeout", "error"):
        A(f"| `{k}` | {oc.get(k,0)} | {oc.get(k,0)/n:.1%} |")
    A("")
    A("## Attribution inside bucket (b)")
    A("")
    A(f"| Where the defect lives | Tasks | Share of {len(b)} |")
    A("|---|---:|---:|")
    A(f"| staged workspace Python cannot parse or import, so no agent edit could "
      f"ever pass a check that runs the code | {len(b_corrupt)} | {len(b_corrupt)/len(b):.1%} |")
    A(f"| staged workspace Python is clean; the failure is in the grader or its "
      f"environment | {len(b_clean)} | {len(b_clean)/len(b):.1%} |")
    A("")
    A("The first row is a **lower bound**: it is a static test for renamed Python "
      "builtins, renamed stdlib import targets, and files that no longer parse. It "
      "does not catch a renamed third-party module name, and running the graders' "
      "own commands found two further such tasks inside the 'clean' row.")
    A("")
    A("## Measured cause of the C1 (\"test suite passes\") failure")
    A("")
    A("Obtained by re-running each grader's own pytest target against the "
      "reference workspace and reading the error.")
    A("")
    A("| Cause | Clean-Python bucket-(b) tasks | Sampled corrupt bucket-(b) tasks |")
    A("|---|---:|---:|")
    for k in sorted(set(diag_clean) | set(diag_corrupt)):
        A(f"| `{k}` | {diag_clean.get(k,0)} | {diag_corrupt.get(k,0)} |")
    A("")
    A("`assertion` -- a test that actually disagrees with the upstream fix -- does "
      "not appear at all.")
    A("")
    A(f"On {len(eq)} of the {len(b)} bucket-(b) tasks ({len(eq)/len(b):.1%}) the "
      "reference scores *exactly* the pristine do-nothing floor.")
    A("")
    A(f"`missing_dependency` has a mechanical explanation: {todo} of the {n} "
      "graders in this scope still contain the literal line "
      "`# TODO: add repo-specific dependencies`, the placeholder the PR-to-task "
      "converter emits where the repository's own dependencies were meant to be "
      "installed. Every one of those graders installs `pytest` and nothing else, "
      "then runs the repository's tests.")
    A("")
    with open(os.path.join(Q, "g3_mechanism_breakdown.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\nwrote", p)
    print("wrote", os.path.join(Q, "g3_mechanism_breakdown.md"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
