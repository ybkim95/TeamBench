"""
TeamBench leaderboard aggregation.

Computes:
  - Success Rate (per task, overall)
  - Pass^k (stability across seeds)
  - Communication Cost (messages, tokens)
  - Verifier Value (error-catch rate)
  - Teamwork Necessity Index (TNI)
  - Compatibility Matrix (cross-model analysis)

Usage:
    python -m leaderboard.aggregate --results_dir shared/runs --output leaderboard/results.json
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
from collections import defaultdict


def load_scores(results_dir: str) -> list[dict]:
    """Load all score.json files from run directories."""
    scores = []
    results_path = pathlib.Path(results_dir)
    for score_file in sorted(results_path.rglob("score.json")):
        try:
            score = json.loads(score_file.read_text(encoding="utf-8"))
            run_dir = score_file.parent.parent
            # Try to load run metadata
            meta_path = run_dir / "meta.json"
            if meta_path.exists():
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                score["_meta"] = meta
            score["_run_dir"] = str(run_dir)
            scores.append(score)
        except (json.JSONDecodeError, OSError):
            continue
    return scores


def compute_success_rate(scores: list[dict]) -> float:
    """Overall success rate."""
    if not scores:
        return 0.0
    passed = sum(1 for s in scores if s.get("pass", False))
    return passed / len(scores)


def compute_pass_at_k(scores_by_task: dict[str, list[dict]], k: int = 3) -> dict[str, float]:
    """
    Pass^k: for each task, probability of at least one success in k tries.
    Approximated as: 1 - (1 - success_rate)^k
    """
    result = {}
    for task_id, task_scores in scores_by_task.items():
        sr = compute_success_rate(task_scores)
        result[task_id] = 1.0 - (1.0 - sr) ** k
    return result


def compute_tni(
    s_full: float,
    s_restricted: float,
    s_team: float,
    epsilon: float = 0.01,
) -> float:
    """
    Teamwork Necessity Index.

    TNI = (S_team - S_restricted) / max(epsilon, S_full - S_restricted)

    Interpretation:
      ~1.0: teamwork fully recovers the performance gap
      ~0.0: teamwork doesn't help
      <0.0: teamwork is harmful
    """
    gap = max(epsilon, s_full - s_restricted)
    return (s_team - s_restricted) / gap


def compute_verifier_value(scores: list[dict]) -> float:
    """
    Verifier Error-Catch Rate:
    (cases where verifier caught hidden violation and led to pass)
    / (cases with hidden violations)

    This requires task-level metadata about hidden violations.
    For now, returns ratio of tasks where verifier attestation was meaningful.
    """
    if not scores:
        return 0.0
    attestation_present = sum(
        1 for s in scores
        if s.get("pass", False) and "bad_attestation" not in s.get("failure_modes", [])
    )
    return attestation_present / len(scores)


def build_compatibility_matrix(
    results: list[dict],
) -> dict:
    """
    Build cross-model compatibility matrix.

    Input: list of dicts with keys:
      planner_model, executor_model, verifier_model, task_id, pass

    Output: nested dict C[planner][executor][verifier] = success_rate
    """
    counts = defaultdict(lambda: {"total": 0, "passed": 0})

    for r in results:
        key = (r["planner_model"], r["executor_model"], r["verifier_model"])
        counts[key]["total"] += 1
        if r.get("pass", False):
            counts[key]["passed"] += 1

    matrix = {}
    for (p, e, v), stats in counts.items():
        if p not in matrix:
            matrix[p] = {}
        if e not in matrix[p]:
            matrix[p][e] = {}
        matrix[p][e][v] = stats["passed"] / max(1, stats["total"])

    return matrix


def compute_partial_score_average(scores: list[dict]) -> float:
    """Average partial score across all runs."""
    partial_scores = []
    for s in scores:
        ps = s.get("secondary", {}).get("partial_score")
        if ps is not None:
            partial_scores.append(ps)
        elif s.get("pass", False):
            partial_scores.append(1.0)
        else:
            partial_scores.append(0.0)
    return sum(partial_scores) / max(1, len(partial_scores))


def compute_failure_taxonomy(scores: list[dict]) -> dict[str, int]:
    """Aggregate failure modes across all runs."""
    taxonomy = defaultdict(int)
    for s in scores:
        for fm in s.get("failure_modes", []):
            taxonomy[fm] += 1
    return dict(sorted(taxonomy.items(), key=lambda x: -x[1]))


def load_task_configs(tasks_dir: str = "tasks") -> dict[str, dict]:
    """Load task.yaml metadata for all tasks.

    Uses a lightweight YAML subset parser (no PyYAML dependency).
    Handles simple key: value, key: [list] forms used in task.yaml files.
    """
    configs = {}
    tasks_path = pathlib.Path(tasks_dir)
    if not tasks_path.is_dir():
        return configs
    for task_dir in sorted(tasks_path.iterdir()):
        yaml_path = task_dir / "task.yaml"
        if yaml_path.is_file():
            try:
                cfg = _parse_simple_yaml(yaml_path.read_text(encoding="utf-8"))
                if "task_id" in cfg:
                    configs[cfg["task_id"]] = cfg
            except Exception:
                continue
    return configs


def _parse_simple_yaml(text: str) -> dict:
    """Parse the simple YAML subset used by task.yaml files."""
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            # Parse inline list: [a, b, c]
            inner = val[1:-1].strip()
            if not inner:
                result[key] = []
            else:
                items = [v.strip().strip("'\"") for v in inner.split(",")]
                # Try to convert numeric items
                parsed = []
                for item in items:
                    try:
                        parsed.append(int(item))
                    except ValueError:
                        try:
                            parsed.append(float(item))
                        except ValueError:
                            parsed.append(item)
                result[key] = parsed
        elif val.lower() in ("true", "false"):
            result[key] = val.lower() == "true"
        else:
            try:
                result[key] = int(val)
            except ValueError:
                try:
                    result[key] = float(val)
                except ValueError:
                    result[key] = val
    return result


def compute_per_difficulty(scores: list[dict], task_configs: dict[str, dict]) -> dict[str, float]:
    """Success rate breakdown by difficulty tier."""
    by_diff = defaultdict(list)
    for s in scores:
        task_id = s.get("_meta", {}).get("task_id", "")
        cfg = task_configs.get(task_id, {})
        diff = cfg.get("difficulty", "medium")
        by_diff[diff].append(s.get("pass", False))
    return {
        diff: round(sum(passes) / max(1, len(passes)), 4)
        for diff, passes in sorted(by_diff.items())
    }


def compute_per_domain(scores: list[dict], task_configs: dict[str, dict]) -> dict[str, float]:
    """Success rate breakdown by domain."""
    by_domain = defaultdict(list)
    for s in scores:
        task_id = s.get("_meta", {}).get("task_id", "")
        cfg = task_configs.get(task_id, {})
        domain = cfg.get("domain", "unknown")
        by_domain[domain].append(s.get("pass", False))
    return {
        domain: round(sum(passes) / max(1, len(passes)), 4)
        for domain, passes in sorted(by_domain.items())
    }


def compute_per_language(scores: list[dict], task_configs: dict[str, dict]) -> dict[str, float]:
    """Success rate for tasks involving each language."""
    by_lang = defaultdict(list)
    for s in scores:
        task_id = s.get("_meta", {}).get("task_id", "")
        cfg = task_configs.get(task_id, {})
        for lang in cfg.get("languages", ["python"]):
            by_lang[lang].append(s.get("pass", False))
    return {
        lang: round(sum(passes) / max(1, len(passes)), 4)
        for lang, passes in sorted(by_lang.items())
    }


# --- Category prefix mapping for paper-ready breakdowns ---
CATEGORY_MAP = {
    "SEC": "Security",
    "INC": "Incident Response",
    "CR": "Code Review",
    "SPEC": "Spec-to-Implementation",
    "PIPE": "Pipeline/Integration",
    "INT": "Pipeline/Integration",
    "O": "Operations",
    "D": "Data Engineering",
    "SQL": "Data Engineering",
    "S": "Software Engineering",
    "GO": "Software Engineering",
    "JS": "Software Engineering",
    "LH": "Long-Horizon",
    "SCALE": "Long-Horizon",
    "SYNTH": "Long-Horizon",
    "P": "Policy/Compliance",
    "NEG": "Tradeoff/Negotiation",
    "MULTI": "Multi-language",
    "TEST": "Testing",
    "IR": "Information Retrieval",
}


def _task_id_to_category(task_id: str) -> str:
    """Map a task_id like SEC2_auth_bypass to its category name."""
    prefix = task_id.split("_")[0] if "_" in task_id else task_id
    # Strip trailing digits: SEC2 -> SEC, LH1 -> LH
    alpha = ""
    for ch in prefix:
        if ch.isalpha():
            alpha += ch
        else:
            break
    return CATEGORY_MAP.get(alpha.upper(), alpha.upper())


def compute_per_category(scores: list[dict], task_configs: dict[str, dict]) -> dict[str, dict]:
    """Per-category breakdown with success rate AND average partial score."""
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for s in scores:
        task_id = s.get("_meta", {}).get("task_id", "")
        if not task_id:
            # Try extracting from run_dir path
            run_dir = s.get("_run_dir", "")
            parts = run_dir.split("/")
            for p in parts:
                if any(p.startswith(pre) for pre in CATEGORY_MAP):
                    task_id = p
                    break
        cat = _task_id_to_category(task_id)
        by_cat[cat].append(s)

    result = {}
    for cat, cat_scores in sorted(by_cat.items()):
        passed = sum(1 for s in cat_scores if s.get("pass", False))
        partials = []
        for s in cat_scores:
            ps = s.get("secondary", {}).get("partial_score")
            if ps is not None:
                partials.append(float(ps))
            else:
                partials.append(1.0 if s.get("pass") else 0.0)
        result[cat] = {
            "count": len(cat_scores),
            "success_rate": round(passed / max(1, len(cat_scores)), 4),
            "avg_partial_score": round(sum(partials) / max(1, len(partials)), 4),
        }
    return result


def compute_partial_pass_at_k(
    scores_by_task: dict[str, list[dict]], k: int = 3
) -> dict[str, float]:
    """
    Partial-score-aware Pass@k.
    For each task: max partial score across k seeds.
    """
    result = {}
    for task_id, task_scores in scores_by_task.items():
        partials = []
        for s in task_scores[:k]:
            ps = s.get("secondary", {}).get("partial_score")
            if ps is not None:
                partials.append(float(ps))
            else:
                partials.append(1.0 if s.get("pass") else 0.0)
        result[task_id] = max(partials) if partials else 0.0
    return result


def generate_paper_table(
    scores: list[dict],
    task_configs: dict[str, dict],
) -> str:
    """Generate LaTeX-ready results table for the paper."""
    per_cat = compute_per_category(scores, task_configs)
    per_diff = compute_per_difficulty(scores, task_configs)

    lines = []
    lines.append("% Auto-generated by TeamBench leaderboard.aggregate")
    lines.append("\\begin{tabular}{lrrr}")
    lines.append("\\toprule")
    lines.append("Category & Tasks & Success Rate & Avg Partial \\\\")
    lines.append("\\midrule")

    for cat, stats in sorted(per_cat.items()):
        lines.append(
            f"{cat} & {stats['count']} & "
            f"{stats['success_rate']:.1%} & "
            f"{stats['avg_partial_score']:.2f} \\\\"
        )

    lines.append("\\midrule")
    overall_sr = compute_success_rate(scores)
    overall_ps = compute_partial_score_average(scores)
    lines.append(
        f"\\textbf{{Overall}} & {len(scores)} & "
        f"{overall_sr:.1%} & {overall_ps:.2f} \\\\"
    )
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")

    lines.append("")
    lines.append("% Difficulty breakdown:")
    for diff, rate in sorted(per_diff.items()):
        lines.append(f"% {diff}: {rate:.1%}")

    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="TeamBench leaderboard aggregation")
    ap.add_argument("--results_dir", default="shared/runs", help="Directory containing run results")
    ap.add_argument("--output", default="leaderboard/results.json", help="Output file path")
    ap.add_argument("--paper-table", action="store_true", help="Generate LaTeX table for paper")
    args = ap.parse_args()

    scores = load_scores(args.results_dir)
    if not scores:
        print("No scores found.")
        return

    overall_sr = compute_success_rate(scores)
    failure_taxonomy = compute_failure_taxonomy(scores)
    verifier_value = compute_verifier_value(scores)
    partial_avg = compute_partial_score_average(scores)

    # Load task configs for dimensional breakdowns
    task_configs = load_task_configs()
    per_difficulty = compute_per_difficulty(scores, task_configs)
    per_domain = compute_per_domain(scores, task_configs)
    per_language = compute_per_language(scores, task_configs)

    per_category = compute_per_category(scores, task_configs)

    result = {
        "total_runs": len(scores),
        "overall_success_rate": round(overall_sr, 4),
        "partial_score_average": round(partial_avg, 4),
        "verifier_value": round(verifier_value, 4),
        "per_difficulty": per_difficulty,
        "per_domain": per_domain,
        "per_category": per_category,
        "per_language": per_language,
        "failure_taxonomy": failure_taxonomy,
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2))

    # Generate paper table if requested
    if getattr(args, "paper_table", False):
        table = generate_paper_table(scores, task_configs)
        table_path = args.output.replace(".json", "_table.tex")
        with open(table_path, "w") as f:
            f.write(table)
        print(f"\nLaTeX table written to: {table_path}")


if __name__ == "__main__":
    main()
