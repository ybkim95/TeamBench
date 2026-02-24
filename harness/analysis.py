"""
TeamBench post-hoc analysis pipeline.

Aggregates campaign results and computes:
  - Per-model success rates
  - Per-task difficulty calibration
  - Per-domain breakdown
  - Per-seed stability (Pass^k)
  - Cross-model compatibility matrix
  - Failure mode taxonomy
  - TNI computation (if oracle/restricted baselines available)

Usage:
    python -m harness.analysis --campaign shared/campaigns/campaign_XXXX/
    python -m harness.analysis --campaign shared/campaigns/campaign_XXXX/ --tni-oracle shared/oracle.json --tni-restricted shared/restricted.json
"""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path


def load_campaign(campaign_dir: str) -> dict:
    """Load campaign results."""
    results_path = os.path.join(campaign_dir, "results.json")
    if os.path.isfile(results_path):
        with open(results_path) as f:
            return json.load(f)
    # Fall back to checkpoint
    checkpoint_path = os.path.join(campaign_dir, "checkpoint.jsonl")
    results = []
    if os.path.isfile(checkpoint_path):
        with open(checkpoint_path) as f:
            for line in f:
                results.append(json.loads(line.strip()))
    return {"results": results}


def per_model_stats(results: list[dict]) -> dict:
    """Compute per-model success rates and partial scores."""
    by_model = defaultdict(list)
    for r in results:
        model = r.get("model", "unknown")
        by_model[model].append(r)

    stats = {}
    for model, runs in sorted(by_model.items()):
        passed = sum(1 for r in runs if r.get("pass"))
        partial_scores = [
            r.get("partial_score", 1.0 if r.get("pass") else 0.0)
            for r in runs
        ]
        stats[model] = {
            "total_runs": len(runs),
            "passed": passed,
            "success_rate": round(passed / max(1, len(runs)), 4),
            "avg_partial_score": round(sum(partial_scores) / max(1, len(partial_scores)), 4),
            "avg_turns": round(sum(r.get("total_turns", 0) for r in runs) / max(1, len(runs)), 1),
            "avg_elapsed_sec": round(sum(r.get("elapsed_sec", 0) for r in runs) / max(1, len(runs)), 1),
        }
    return stats


def per_task_stats(results: list[dict]) -> dict:
    """Compute per-task success rates for difficulty calibration."""
    by_task = defaultdict(list)
    for r in results:
        task = r.get("task_id", "unknown")
        by_task[task].append(r)

    stats = {}
    for task, runs in sorted(by_task.items()):
        passed = sum(1 for r in runs if r.get("pass"))
        success_rate = passed / max(1, len(runs))

        # Infer difficulty from success rate
        if success_rate >= 0.8:
            inferred_difficulty = "easy"
        elif success_rate >= 0.5:
            inferred_difficulty = "medium"
        elif success_rate >= 0.2:
            inferred_difficulty = "hard"
        else:
            inferred_difficulty = "expert"

        stats[task] = {
            "total_runs": len(runs),
            "passed": passed,
            "success_rate": round(success_rate, 4),
            "inferred_difficulty": inferred_difficulty,
        }
    return stats


def per_domain_stats(results: list[dict]) -> dict:
    """Compute per-domain success rates."""
    by_domain = defaultdict(list)
    for r in results:
        task = r.get("task_id", "")
        # Extract domain prefix (e.g., S1_hidden_spec → S)
        domain = task.split("_")[0].rstrip("0123456789") if "_" in task else task[:2]
        by_domain[domain].append(r)

    stats = {}
    for domain, runs in sorted(by_domain.items()):
        passed = sum(1 for r in runs if r.get("pass"))
        stats[domain] = {
            "total_runs": len(runs),
            "passed": passed,
            "success_rate": round(passed / max(1, len(runs)), 4),
        }
    return stats


def pass_at_k(results: list[dict], k: int = 3) -> dict:
    """Compute Pass^k: probability of success in k seeded attempts per task."""
    by_task_model = defaultdict(list)
    for r in results:
        key = f"{r.get('model', 'unknown')}:{r.get('task_id', 'unknown')}"
        by_task_model[key].append(r)

    stats = {}
    for key, runs in sorted(by_task_model.items()):
        sr = sum(1 for r in runs if r.get("pass")) / max(1, len(runs))
        pass_k = 1.0 - (1.0 - sr) ** k
        stats[key] = {
            "success_rate": round(sr, 4),
            f"pass_at_{k}": round(pass_k, 4),
            "num_seeds": len(runs),
        }
    return stats


def failure_taxonomy(results: list[dict]) -> dict:
    """Aggregate failure modes across all runs."""
    taxonomy = defaultdict(int)
    for r in results:
        for fm in r.get("failure_modes", []):
            taxonomy[fm] += 1
    return dict(sorted(taxonomy.items(), key=lambda x: -x[1]))


def cross_model_matrix(results: list[dict]) -> dict:
    """Build per-task cross-model comparison table."""
    by_task = defaultdict(dict)
    for r in results:
        task = r.get("task_id", "unknown")
        model = r.get("model", "unknown")
        if model not in by_task[task]:
            by_task[task][model] = {"passed": 0, "total": 0}
        by_task[task][model]["total"] += 1
        if r.get("pass"):
            by_task[task][model]["passed"] += 1

    matrix = {}
    for task, models in sorted(by_task.items()):
        matrix[task] = {
            m: round(d["passed"] / max(1, d["total"]), 4)
            for m, d in sorted(models.items())
        }
    return matrix


def compute_tni(s_full: float, s_restricted: float, s_team: float, epsilon: float = 0.01) -> dict:
    """Compute Teamwork Necessity Index."""
    gap = max(epsilon, s_full - s_restricted)
    tni = (s_team - s_restricted) / gap
    return {
        "s_full": round(s_full, 4),
        "s_restricted": round(s_restricted, 4),
        "s_team": round(s_team, 4),
        "tni": round(tni, 4),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="TeamBench analysis pipeline")
    ap.add_argument("--campaign", required=True, help="Campaign directory")
    ap.add_argument("--tni-oracle", help="Oracle (full-access) results JSON")
    ap.add_argument("--tni-restricted", help="Restricted (single-agent) results JSON")
    ap.add_argument("--output", help="Output file (default: <campaign>/analysis.json)")
    ap.add_argument("--k", type=int, default=3, help="k for Pass^k computation")
    args = ap.parse_args()

    campaign = load_campaign(args.campaign)
    results = campaign.get("results", [])

    if not results:
        print("No results found in campaign.")
        return

    output_path = args.output or os.path.join(args.campaign, "analysis.json")

    analysis = {
        "campaign": args.campaign,
        "total_runs": len(results),
        "per_model": per_model_stats(results),
        "per_task": per_task_stats(results),
        "per_domain": per_domain_stats(results),
        f"pass_at_{args.k}": pass_at_k(results, k=args.k),
        "failure_taxonomy": failure_taxonomy(results),
        "cross_model_matrix": cross_model_matrix(results),
    }

    # TNI computation if baselines provided
    if args.tni_oracle and args.tni_restricted:
        with open(args.tni_oracle) as f:
            oracle = json.load(f)
        with open(args.tni_restricted) as f:
            restricted = json.load(f)
        s_full = oracle.get("success_rate", 0.0)
        s_restricted = restricted.get("success_rate", 0.0)
        s_team = sum(1 for r in results if r.get("pass")) / max(1, len(results))
        analysis["tni"] = compute_tni(s_full, s_restricted, s_team)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(analysis, f, indent=2)

    # Print summary
    print(f"\nTeamBench Analysis Report")
    print(f"{'=' * 60}")
    print(f"\nPer-Model Results:")
    for model, stats in analysis["per_model"].items():
        print(f"  {model:30s}  {stats['passed']}/{stats['total_runs']} "
              f"({stats['success_rate']:.1%})  avg_partial={stats['avg_partial_score']:.2f}")

    print(f"\nPer-Task Difficulty Calibration:")
    for task, stats in analysis["per_task"].items():
        print(f"  {task:30s}  {stats['success_rate']:.1%}  [{stats['inferred_difficulty']}]")

    print(f"\nTop Failure Modes:")
    for fm, count in list(analysis["failure_taxonomy"].items())[:10]:
        print(f"  {fm:40s}  {count}")

    if "tni" in analysis:
        tni = analysis["tni"]
        print(f"\nTeamwork Necessity Index:")
        print(f"  S_full={tni['s_full']:.1%}  S_restricted={tni['s_restricted']:.1%}  "
              f"S_team={tni['s_team']:.1%}  TNI={tni['tni']:.4f}")

    print(f"\nFull analysis: {output_path}")


if __name__ == "__main__":
    main()
