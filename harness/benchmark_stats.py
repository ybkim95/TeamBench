"""
TeamBench benchmark statistics — task distribution analysis for the paper.

Generates Table 1 (task distribution), difficulty breakdown, domain coverage,
and TNI pattern analysis across the full benchmark suite.

Usage:
    python -m harness.benchmark_stats
    python -m harness.benchmark_stats --latex  # LaTeX table output
    python -m harness.benchmark_stats --json   # JSON output
"""
from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from pathlib import Path


# Category mapping: prefix -> (full_name, short_name)
CATEGORIES = {
    "SEC": ("Security", "SEC"),
    "INC": ("Incident Response", "INC"),
    "CR": ("Code Review", "CR"),
    "SPEC": ("Spec-to-Implementation", "SPEC"),
    "PIPE": ("Pipeline/Integration", "PIPE"),
    "INT": ("Pipeline/Integration", "INT"),
    "O": ("Operations", "OPS"),
    "D": ("Data Engineering", "DATA"),
    "SQL": ("Data Engineering", "SQL"),
    "S": ("Software Engineering", "SWE"),
    "GO": ("Software Engineering", "GO"),
    "JS": ("Software Engineering", "JS"),
    "LH": ("Long-Horizon", "LH"),
    "SCALE": ("Long-Horizon", "SCALE"),
    "SYNTH": ("Long-Horizon", "SYNTH"),
    "P": ("Policy/Compliance", "POL"),
    "NEG": ("Tradeoff/Negotiation", "NEG"),
    "MULTI": ("Multi-language", "MULTI"),
    "TEST": ("Testing", "TEST"),
    "IR": ("Information Retrieval", "IR"),
}

# TNI patterns
TNI_PATTERNS = {
    "A": "Hidden Constraints",
    "B": "Adversarial Traps",
    "C": "Multi-Criteria Optimization",
    "D": "Cross-System Contract",
    "E": "Compliance Rules",
    "F": "Ordered Dependencies",
}


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
            inner = val[1:-1].strip()
            if not inner:
                result[key] = []
            else:
                items = [v.strip().strip("'\"") for v in inner.split(",")]
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


def _task_prefix(task_id: str) -> str:
    """Extract alphabetic prefix from task_id: SEC2_auth_bypass -> SEC."""
    prefix = ""
    for ch in task_id.split("_")[0] if "_" in task_id else task_id:
        if ch.isalpha():
            prefix += ch
        else:
            break
    return prefix.upper()


def _task_category(task_id: str) -> str:
    """Get the category name for a task_id."""
    prefix = _task_prefix(task_id)
    cat_info = CATEGORIES.get(prefix)
    return cat_info[0] if cat_info else prefix


def load_all_tasks(tasks_dir: str = "tasks") -> list[dict]:
    """Load all task.yaml configs from the tasks directory."""
    tasks = []
    tasks_path = Path(tasks_dir)
    if not tasks_path.is_dir():
        return tasks
    for task_dir in sorted(tasks_path.iterdir()):
        yaml_path = task_dir / "task.yaml"
        if yaml_path.is_file():
            cfg = _parse_simple_yaml(yaml_path.read_text(encoding="utf-8"))
            cfg["_dir_name"] = task_dir.name
            cfg.setdefault("task_id", task_dir.name)
            cfg.setdefault("difficulty", "medium")
            cfg.setdefault("domain", "unknown")
            tasks.append(cfg)
    return tasks


def compute_stats(tasks: list[dict]) -> dict:
    """Compute comprehensive benchmark statistics."""
    total = len(tasks)

    # Difficulty distribution
    by_difficulty = defaultdict(int)
    for t in tasks:
        by_difficulty[t.get("difficulty", "medium")] += 1

    # Domain distribution
    by_domain = defaultdict(int)
    for t in tasks:
        by_domain[t.get("domain", "unknown")] += 1

    # Category distribution (using prefix mapping)
    by_category = defaultdict(list)
    for t in tasks:
        cat = _task_category(t["task_id"])
        by_category[cat].append(t["task_id"])

    # Language distribution
    by_language = defaultdict(int)
    for t in tasks:
        for lang in t.get("languages", ["python"]):
            by_language[lang] += 1

    # Parameterized vs static
    parameterized = sum(1 for t in tasks if t.get("parameterized", False))
    seed_counts = []
    for t in tasks:
        seeds = t.get("seeds", [0])
        if isinstance(seeds, list):
            seed_counts.append(len(seeds))
        else:
            seed_counts.append(1)

    # Check for grade.sh and setup.sh existence
    has_grader = sum(1 for t in tasks if (Path("tasks") / t["_dir_name"] / "grade.sh").is_file())
    has_setup = sum(1 for t in tasks if (Path("tasks") / t["_dir_name"] / "setup.sh").is_file())

    return {
        "total_tasks": total,
        "by_difficulty": dict(sorted(by_difficulty.items())),
        "by_domain": dict(sorted(by_domain.items())),
        "by_category": {
            cat: {"count": len(tids), "tasks": sorted(tids)}
            for cat, tids in sorted(by_category.items())
        },
        "by_language": dict(sorted(by_language.items())),
        "parameterized": parameterized,
        "static": total - parameterized,
        "avg_seeds": round(sum(seed_counts) / max(1, len(seed_counts)), 1),
        "total_instances": sum(seed_counts),
        "has_grader": has_grader,
        "has_setup": has_setup,
    }


def print_report(stats: dict) -> None:
    """Print formatted benchmark statistics."""
    print(f"\n{'='*70}")
    print(f"TeamBench Benchmark Statistics")
    print(f"{'='*70}")
    print(f"Total tasks: {stats['total_tasks']}")
    print(f"Parameterized: {stats['parameterized']} ({stats['parameterized']/max(1,stats['total_tasks']):.0%})")
    print(f"Total instances (all seeds): {stats['total_instances']}")
    print(f"Has grader: {stats['has_grader']}/{stats['total_tasks']}")

    print(f"\n--- Difficulty Distribution ---")
    for diff in ["easy", "medium", "hard", "expert"]:
        count = stats["by_difficulty"].get(diff, 0)
        pct = count / max(1, stats["total_tasks"])
        bar = "#" * int(pct * 40)
        print(f"  {diff:<8} {count:>3} ({pct:>5.1%}) {bar}")

    print(f"\n--- Category Distribution ---")
    for cat, info in sorted(stats["by_category"].items(), key=lambda x: -x[1]["count"]):
        count = info["count"]
        pct = count / max(1, stats["total_tasks"])
        print(f"  {cat:<25} {count:>3} ({pct:>5.1%})")

    print(f"\n--- Domain Distribution ---")
    for domain, count in sorted(stats["by_domain"].items(), key=lambda x: -x[1]):
        pct = count / max(1, stats["total_tasks"])
        print(f"  {domain:<20} {count:>3} ({pct:>5.1%})")

    print(f"\n--- Language Distribution ---")
    for lang, count in sorted(stats["by_language"].items(), key=lambda x: -x[1]):
        print(f"  {lang:<15} {count:>3}")


def generate_latex_table(stats: dict) -> str:
    """Generate LaTeX table for the paper (Table 1)."""
    lines = [
        "% Auto-generated by harness.benchmark_stats",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{TeamBench task distribution across categories and difficulty levels.}",
        "\\label{tab:task-distribution}",
        "\\begin{tabular}{lccccr}",
        "\\toprule",
        "Category & Easy & Medium & Hard & Expert & Total \\\\",
        "\\midrule",
    ]

    # Build per-category difficulty matrix
    tasks = []  # We need the raw tasks to compute this
    cat_diff = defaultdict(lambda: defaultdict(int))

    # Since we only have stats, reconstruct from by_category
    for cat, info in sorted(stats["by_category"].items(), key=lambda x: -x[1]["count"]):
        total = info["count"]
        # We don't have per-category difficulty in stats alone, so show total
        lines.append(f"{cat} & & & & & {total} \\\\")

    lines.extend([
        "\\midrule",
        f"\\textbf{{Total}} & "
        f"{stats['by_difficulty'].get('easy', 0)} & "
        f"{stats['by_difficulty'].get('medium', 0)} & "
        f"{stats['by_difficulty'].get('hard', 0)} & "
        f"{stats['by_difficulty'].get('expert', 0)} & "
        f"{stats['total_tasks']} \\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
    ])

    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="TeamBench benchmark statistics")
    ap.add_argument("--tasks-dir", default="tasks", help="Tasks directory")
    ap.add_argument("--latex", action="store_true", help="Output LaTeX table")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    ap.add_argument("--output", help="Write output to file")
    args = ap.parse_args()

    tasks = load_all_tasks(args.tasks_dir)
    if not tasks:
        print("No tasks found.")
        return

    stats = compute_stats(tasks)

    if args.json:
        output = json.dumps(stats, indent=2)
    elif args.latex:
        output = generate_latex_table(stats)
    else:
        print_report(stats)
        return

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Written to: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
