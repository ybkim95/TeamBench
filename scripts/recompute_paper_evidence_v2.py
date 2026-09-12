"""recompute_paper_evidence_v2.py.

Adds two artefacts the paper still lacks evidence for:

  A. Strict contamination-resistant subset.
     Per-task Jaccard distribution from contamination_validation.json.
     Identify the count of tasks below several Jaccard thresholds so the
     paper can report a "strict subset" alongside the headline mean.

  B. Information relay fidelity.
     Fraction of spec-critical tokens that survive
     spec.md  ->  Planner messages  ->  Executor messages
     measured per task on the role-mixing runs that have full transcripts.

Outputs:
  shared/paper/contamination_strict_subset.json
  shared/paper/relay_fidelity.json
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SHARED = REPO / "shared"
PAPER = SHARED / "paper"

STOPWORDS = {
    "the", "a", "an", "of", "to", "and", "or", "is", "are", "be",
    "in", "on", "at", "for", "with", "by", "as", "this", "that",
    "it", "its", "we", "you", "your", "our", "if", "then", "else",
    "from", "into", "out", "up", "down", "off", "over", "under",
    "but", "not", "no", "yes", "do", "does", "did", "have", "has",
    "had", "will", "would", "should", "can", "could", "may", "might",
    "must", "shall", "than", "so", "such", "via", "using", "use",
    "task", "tasks", "spec", "specification",
}
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")


def _spec_tokens(spec_text: str, top_k: int = 50) -> set[str]:
    """Return up to top_k content tokens that appear at least twice in the spec.
    Filters short tokens, stopwords, all-lowercase common words.
    """
    toks = [t for t in TOKEN_RE.findall(spec_text) if len(t) >= 4]
    toks = [t for t in toks if t.lower() not in STOPWORDS]
    counts = Counter(toks)
    # tokens that appear at least twice are likely structural to the task
    candidates = [t for t, c in counts.most_common() if c >= 2]
    return set(candidates[:top_k])


def _read_dialogue_role_text(dialogue_path: Path, role: str) -> str:
    """Concatenate all dialogue lines for the given role into a single string."""
    if not dialogue_path.exists():
        return ""
    chunks = []
    for line in dialogue_path.read_text(errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        r = (d.get("role") or "").lower()
        if r == role or (role == "executor" and r == "generator"):
            content = d.get("content")
            if isinstance(content, str):
                chunks.append(content)
    return "\n".join(chunks)


def compute_strict_contamination() -> dict:
    cv = json.loads((PAPER / "contamination_validation.json").read_text())
    rows = cv["per_task_validation"]
    if isinstance(rows, dict):
        rows = list(rows.values())
    jacs = [r["mean_jaccard_dev_vs_held"] for r in rows
            if r.get("mean_jaccard_dev_vs_held") is not None]
    n = len(jacs)
    thresholds = [0.3, 0.5, 0.7, 0.9]
    counts = {f"jaccard_below_{t}": sum(1 for j in jacs if j < t) for t in thresholds}
    # Per-task list for tasks with j < 0.5 (the "strict subset")
    strict_tasks = sorted(
        (r["task_id"], round(r["mean_jaccard_dev_vs_held"], 3))
        for r in rows
        if r.get("mean_jaccard_dev_vs_held") is not None
        and r["mean_jaccard_dev_vs_held"] < 0.5
    )
    return {
        "n_tasks_evaluated": n,
        "min_jaccard": round(min(jacs), 3),
        "max_jaccard": round(max(jacs), 3),
        "median_jaccard": round(sorted(jacs)[n // 2], 3),
        "p25_jaccard": round(sorted(jacs)[n // 4], 3),
        "p75_jaccard": round(sorted(jacs)[3 * n // 4], 3),
        "n_strict_subset_jaccard_lt_0p5": counts["jaccard_below_0.5"],
        "threshold_counts": counts,
        "strict_subset_tasks": strict_tasks,
    }


def compute_relay_fidelity(max_runs_per_task: int = 3) -> dict:
    """For each role-mixing run with a dialogue.jsonl, compute:
    - planner_recall   = |spec_top_k ∩ planner_text| / |spec_top_k|
    - executor_recall  = |spec_top_k ∩ executor_text| / |spec_top_k|
    - relay_fidelity   = |spec_top_k ∩ planner_text ∩ executor_text| / |spec_top_k|

    spec_top_k is the per-task spec-critical token set.
    """
    runs_dir = SHARED / "role_ablation" / "runs"
    tasks_dir = REPO / "tasks"
    if not runs_dir.exists():
        return {"error": "runs_dir missing"}

    spec_cache: dict[str, set[str]] = {}

    def _spec_for(task_id: str) -> set[str]:
        if task_id in spec_cache:
            return spec_cache[task_id]
        spec_path = tasks_dir / task_id / "spec.md"
        if not spec_path.exists():
            spec_cache[task_id] = set()
            return spec_cache[task_id]
        spec_cache[task_id] = _spec_tokens(spec_path.read_text(errors="ignore"))
        return spec_cache[task_id]

    per_task: dict[str, list[dict]] = {}
    n_runs_used = 0
    for cfg_dir in sorted(runs_dir.iterdir()):
        if not cfg_dir.is_dir():
            continue
        for task_dir in sorted(cfg_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            task_id = task_dir.name
            spec_set = _spec_for(task_id)
            if not spec_set:
                continue
            count_for_task = 0
            for run_dir in sorted(task_dir.iterdir()):
                if count_for_task >= max_runs_per_task:
                    break
                dj = run_dir / "messages" / "dialogue.jsonl"
                if not dj.exists():
                    continue
                planner_text = _read_dialogue_role_text(dj, "planner")
                exec_text = _read_dialogue_role_text(dj, "executor")
                if not planner_text and not exec_text:
                    continue
                planner_toks = set(TOKEN_RE.findall(planner_text))
                exec_toks = set(TOKEN_RE.findall(exec_text))
                planner_hit = spec_set & planner_toks
                exec_hit = spec_set & exec_toks
                relay_hit = planner_hit & exec_hit
                spec_n = len(spec_set)
                rec = {
                    "config": cfg_dir.name,
                    "run_id": run_dir.name,
                    "spec_n": spec_n,
                    "planner_recall": round(len(planner_hit) / spec_n, 3) if spec_n else 0.0,
                    "executor_recall": round(len(exec_hit) / spec_n, 3) if spec_n else 0.0,
                    "relay_fidelity": round(len(relay_hit) / spec_n, 3) if spec_n else 0.0,
                }
                per_task.setdefault(task_id, []).append(rec)
                count_for_task += 1
                n_runs_used += 1

    # Aggregate
    if not per_task:
        return {"error": "no runs scored", "n_runs_used": 0}
    all_planner = []
    all_executor = []
    all_relay = []
    per_task_summary = {}
    for tid, recs in per_task.items():
        pr = [r["planner_recall"] for r in recs]
        er = [r["executor_recall"] for r in recs]
        rf = [r["relay_fidelity"] for r in recs]
        per_task_summary[tid] = {
            "n_runs": len(recs),
            "planner_recall_mean": round(sum(pr) / len(pr), 3),
            "executor_recall_mean": round(sum(er) / len(er), 3),
            "relay_fidelity_mean": round(sum(rf) / len(rf), 3),
        }
        all_planner += pr
        all_executor += er
        all_relay += rf

    def _stats(vs):
        if not vs:
            return {"n": 0}
        m = sum(vs) / len(vs)
        return {
            "n": len(vs),
            "mean": round(m, 3),
            "median": round(sorted(vs)[len(vs) // 2], 3),
            "p25": round(sorted(vs)[len(vs) // 4], 3),
            "p75": round(sorted(vs)[3 * len(vs) // 4], 3),
        }

    return {
        "n_runs_used": n_runs_used,
        "n_tasks": len(per_task),
        "method": (
            "Spec-critical tokens are content tokens (length >= 4, not stopwords) "
            "that appear at least twice in spec.md, capped at top 50 by frequency. "
            "Planner / Executor recall is the fraction of spec-critical tokens that "
            "appear in that role's dialogue text. Relay fidelity is the fraction "
            "that appear in BOTH the Planner and the Executor dialogues."
        ),
        "planner_recall": _stats(all_planner),
        "executor_recall": _stats(all_executor),
        "relay_fidelity": _stats(all_relay),
        "per_task": per_task_summary,
    }


def main() -> int:
    contam = compute_strict_contamination()
    relay = compute_relay_fidelity()

    (PAPER / "contamination_strict_subset.json").write_text(
        json.dumps(contam, indent=2) + "\n"
    )
    (PAPER / "relay_fidelity.json").write_text(json.dumps(relay, indent=2) + "\n")

    print("=== Strict contamination subset ===")
    print(f"  n_tasks_evaluated: {contam['n_tasks_evaluated']}")
    print(f"  Jaccard min/p25/median/p75/max: "
          f"{contam['min_jaccard']} / {contam['p25_jaccard']} / "
          f"{contam['median_jaccard']} / {contam['p75_jaccard']} / "
          f"{contam['max_jaccard']}")
    for k, v in contam["threshold_counts"].items():
        pct = v * 100 // max(contam["n_tasks_evaluated"], 1)
        print(f"  {k}: {v} tasks ({pct}%)")
    print(f"  strict subset (j < 0.5): {contam['n_strict_subset_jaccard_lt_0p5']} tasks")
    print()
    print("=== Information relay fidelity ===")
    if "error" in relay:
        print("  ", relay["error"])
    else:
        print(f"  n_runs={relay['n_runs_used']}, n_tasks={relay['n_tasks']}")
        for k in ("planner_recall", "executor_recall", "relay_fidelity"):
            s = relay[k]
            print(f"  {k}: mean={s['mean']}, p25/median/p75 = "
                  f"{s['p25']}/{s['median']}/{s['p75']}, n={s['n']}")
    print(f"\nWrote 2 JSONs to {PAPER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
