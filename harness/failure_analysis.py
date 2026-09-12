"""
TeamBench — Failure taxonomy analysis.

Analyses WHY models fail on tasks by parsing run data and classifying
failures into seven mutually-exclusive categories:

  1. communication_failure    — planner sent instructions, executor ignored them
  2. planning_failure         — planner missed critical spec info / gave wrong guidance
  3. execution_failure        — executor followed plan but made implementation errors
  4. verification_failure     — verifier rejected correct work or missed real bugs
  5. tool_use_failure         — model couldn't use tools properly (malformed calls)
  6. self_contained_task      — task didn't need team coordination (planner adds noise)
  7. specification_misinterpretation — planner read spec but drew wrong conclusions

Parses from:
  - messages/dialogue.jsonl           — planner communications
  - logs/executor/turn_*.json         — executor actions
  - logs/planner/turn_*.json          — planner actions
  - logs/verifier/attempt_*/turn_*.json — verifier actions
  - reports/score.json                — grader failure_modes
  - run_meta.json                     — condition / task_id

Usage:
    from harness.failure_analysis import analyze_failures
    report = analyze_failures(task_id, runs_dir)

CLI:
    python -m harness.failure_analysis --task TASK_ID --runs-dir PATH
    python -m harness.failure_analysis --run-dir PATH
"""
from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------
@dataclass
class FailureClassification:
    """Single-run failure classification result."""
    run_id: str
    condition: str
    task_success: float
    passed: bool
    grader_failure_modes: list[str] = field(default_factory=list)

    # Primary failure category (one of the 7)
    primary_category: str = "unknown"
    # Secondary signals that informed the classification
    signals: dict[str, Any] = field(default_factory=dict)
    # Confidence in the primary classification [0, 1]
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "condition": self.condition,
            "task_success": self.task_success,
            "passed": self.passed,
            "grader_failure_modes": self.grader_failure_modes,
            "primary_category": self.primary_category,
            "signals": self.signals,
            "confidence": self.confidence,
        }


@dataclass
class TaskFailureReport:
    """Aggregated failure analysis for a task across all its runs."""
    task_id: str
    runs_dir: str
    total_runs: int = 0
    passed_runs: int = 0
    classifications: list[FailureClassification] = field(default_factory=list)

    # Category frequency across runs
    category_counts: dict[str, int] = field(default_factory=lambda: Counter())
    # Per-condition pass rates
    condition_pass_rates: dict[str, float] = field(default_factory=dict)
    # Dominant failure category
    dominant_failure: str = "none"
    # Evidence that team coordination was or wasn't useful
    team_helps: bool | None = None
    team_oracle_delta: float | None = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "runs_dir": self.runs_dir,
            "total_runs": self.total_runs,
            "passed_runs": self.passed_runs,
            "pass_rate": self.passed_runs / max(1, self.total_runs),
            "dominant_failure": self.dominant_failure,
            "category_counts": dict(self.category_counts),
            "condition_pass_rates": self.condition_pass_rates,
            "team_helps": self.team_helps,
            "team_oracle_delta": self.team_oracle_delta,
            "runs": [c.to_dict() for c in self.classifications],
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _load_json(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _load_turns(role_dir: str) -> list[dict]:
    """Load all turn_*.json files under role_dir (recursive)."""
    turns: list[dict] = []
    if not os.path.isdir(role_dir):
        return turns
    for root, _dirs, files in os.walk(role_dir):
        for fn in sorted(files):
            if fn.startswith("turn_") and fn.endswith(".json"):
                t = _load_json(os.path.join(root, fn))
                if t:
                    turns.append(t)
    return turns


def _load_dialogue(run_dir: str) -> list[dict]:
    dlg = os.path.join(run_dir, "messages", "dialogue.jsonl")
    messages: list[dict] = []
    if not os.path.isfile(dlg):
        return messages
    with open(dlg) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return messages


def _infer_condition(run_dir: str) -> str:
    meta = _load_json(os.path.join(run_dir, "run_meta.json"))
    if "condition" in meta:
        return str(meta["condition"])
    logs = os.path.join(run_dir, "logs")
    if os.path.isdir(logs):
        subdirs = set(os.listdir(logs))
        for cond in ("oracle", "restricted"):
            if cond in subdirs:
                return cond
        if "planner" in subdirs or "executor" in subdirs:
            # Distinguish team_no_plan / team_no_verify from full
            has_planner = "planner" in subdirs
            has_verifier = "verifier" in subdirs
            if has_planner and has_verifier:
                return "full"
            if has_planner:
                return "team_no_verify"
            return "team_no_plan"
    msgs = _load_dialogue(run_dir)
    if msgs:
        return msgs[0].get("role", "unknown")
    return "unknown"


def _get_score_info(run_dir: str) -> tuple[float, bool, list[str]]:
    """Return (partial_score, passed, failure_modes)."""
    s = _load_json(os.path.join(run_dir, "reports", "score.json"))
    if not s:
        return 0.0, False, []
    passed = bool(s.get("pass"))
    partial = float(s.get("secondary", {}).get(
        "partial_score", 1.0 if passed else 0.0
    ))
    failure_modes = s.get("failure_modes", [])
    return partial, passed, failure_modes


def _tool_call_names(turns: list[dict]) -> list[str]:
    names: list[str] = []
    for t in turns:
        for tc in t.get("tool_calls", []):
            names.append(tc.get("name", "").lower())
    return names


def _has_malformed_calls(turns: list[dict]) -> bool:
    """
    Detect malformed tool calls: missing 'name' field, empty args where
    content is required, or repeated identical calls (stuck loop).
    """
    seen: list[tuple[str, str]] = []
    for t in turns:
        for tc in t.get("tool_calls", []):
            if not tc.get("name"):
                return True
            key = (tc.get("name", ""), json.dumps(tc.get("args", {}), sort_keys=True))
            if seen.count(key) >= 3:
                return True
            seen.append(key)
        # Check tool_results for error signals
        for tr in t.get("tool_results", []):
            if isinstance(tr, dict):
                stderr = str(tr.get("stderr", ""))
                exit_code = tr.get("exit_code", 0)
                # Tool errors that indicate malformed usage
                if exit_code not in (0, None) and any(
                    pat in stderr.lower()
                    for pat in ("no such file", "not found", "invalid", "error:", "permission denied")
                ):
                    return True
    return False


def _planner_instructions_followed(
    messages: list[dict],
    executor_turns: list[dict],
) -> float:
    """
    Estimate how well executor followed planner instructions.

    Heuristic: extract file paths and key terms mentioned in planner messages,
    check whether those paths appear in executor tool calls.

    Returns a follow-through rate in [0, 1].
    """
    planner_msgs = [m for m in messages if m.get("role") == "planner"]
    if not planner_msgs:
        return 1.0  # No planner = no instructions to follow

    # Extract mentioned file paths and identifiers from planner messages
    mentioned: set[str] = set()
    path_pattern = re.compile(r"[\w./\-]+\.\w+")
    for msg in planner_msgs:
        content = str(msg.get("content", ""))
        for match in path_pattern.findall(content):
            if "/" in match or "." in match:
                mentioned.add(match.lower().strip("./"))

    if not mentioned:
        return 0.8  # Planner gave instructions but no file references → partial credit

    # Check executor tool calls for those paths
    executor_paths: set[str] = set()
    for t in executor_turns:
        for tc in t.get("tool_calls", []):
            args = tc.get("args", {})
            for v in args.values():
                if isinstance(v, str):
                    executor_paths.add(v.lower().strip("./"))

    if not executor_paths:
        return 0.0  # Executor made no relevant tool calls

    matched = sum(1 for m in mentioned if any(m in ep or ep in m for ep in executor_paths))
    return min(1.0, matched / len(mentioned))


def _planner_spec_coverage(planner_turns: list[dict]) -> float:
    """
    Estimate how thoroughly the planner read the task spec.

    Heuristic: planner turns that include 'read' tool calls to spec-like
    files (*.txt, *.md, spec.*, requirements.*, policy.*, README*) suggest
    thorough spec reading.
    """
    if not planner_turns:
        return 0.0
    spec_patterns = re.compile(
        r"(spec|requirement|policy|readme|\.txt|\.md|corpus|problem|task)", re.IGNORECASE
    )
    spec_reads = 0
    total_reads = 0
    for t in planner_turns:
        for tc in t.get("tool_calls", []):
            if tc.get("name", "").lower() in ("read", "cat", "head"):
                total_reads += 1
                path = str(tc.get("args", {}).get("path", ""))
                if spec_patterns.search(path):
                    spec_reads += 1
    if total_reads == 0:
        return 0.3  # No reads → planner didn't investigate
    return min(1.0, spec_reads / total_reads + 0.3)


def _verifier_caught_real_bugs(
    verifier_turns: list[dict],
    passed: bool,
    failure_modes: list[str],
) -> tuple[bool, bool]:
    """
    Returns (false_rejection, missed_bugs).

    false_rejection: verifier tool activity was high but task ultimately passed
    missed_bugs: task failed but verifier had low tool activity
    """
    tool_calls = _tool_call_names(verifier_turns)
    activity = len(tool_calls)
    has_test_runs = any(n in ("bash", "run", "pytest", "python", "python3") for n in tool_calls)

    false_rejection = passed and activity > 0 and has_test_runs
    missed_bugs = not passed and len(failure_modes) > 0 and activity < 2

    return false_rejection, missed_bugs


# ---------------------------------------------------------------------------
# Classification logic
# ---------------------------------------------------------------------------
def _classify_run(run_dir: str) -> FailureClassification:
    """Classify a single run into one of the 7 failure categories."""
    run_id = os.path.basename(run_dir)
    condition = _infer_condition(run_dir)
    partial, passed, failure_modes = _get_score_info(run_dir)

    logs_dir = os.path.join(run_dir, "logs")
    planner_turns = _load_turns(os.path.join(logs_dir, "planner"))
    executor_turns = _load_turns(os.path.join(logs_dir, "executor"))

    verifier_base = os.path.join(logs_dir, "verifier")
    verifier_turns: list[dict] = []
    if os.path.isdir(verifier_base):
        for attempt in sorted(os.listdir(verifier_base)):
            verifier_turns.extend(_load_turns(os.path.join(verifier_base, attempt)))

    messages = _load_dialogue(run_dir)

    fc = FailureClassification(
        run_id=run_id,
        condition=condition,
        task_success=partial,
        passed=passed,
        grader_failure_modes=failure_modes,
    )

    if passed:
        fc.primary_category = "success"
        fc.confidence = 1.0
        fc.signals = {"note": "task passed"}
        return fc

    # --- Gather signals ---
    all_turns = planner_turns + executor_turns + verifier_turns
    malformed = _has_malformed_calls(all_turns)
    exec_malformed = _has_malformed_calls(executor_turns)
    plan_malformed = _has_malformed_calls(planner_turns)

    follow_rate = _planner_instructions_followed(messages, executor_turns)
    spec_coverage = _planner_spec_coverage(planner_turns)
    false_rejection, missed_bugs = _verifier_caught_real_bugs(
        verifier_turns, passed, failure_modes
    )

    has_planner = len(planner_turns) > 0
    has_executor = len(executor_turns) > 0
    has_verifier = len(verifier_turns) > 0
    has_messages = len(messages) > 0
    exec_tool_calls = _tool_call_names(executor_turns)
    planner_tool_calls = _tool_call_names(planner_turns)

    fc.signals = {
        "follow_rate": follow_rate,
        "spec_coverage": spec_coverage,
        "false_rejection": false_rejection,
        "missed_bugs": missed_bugs,
        "malformed_calls": malformed,
        "exec_malformed_calls": exec_malformed,
        "plan_malformed_calls": plan_malformed,
        "has_planner": has_planner,
        "has_executor": has_executor,
        "has_verifier": has_verifier,
        "planner_turns_count": len(planner_turns),
        "executor_turns_count": len(executor_turns),
        "verifier_turns_count": len(verifier_turns),
        "message_count": len(messages),
        "exec_tool_count": len(exec_tool_calls),
        "grader_failure_modes": failure_modes,
    }

    # --- Classification decision tree ---

    # 1. Tool-use failure: malformed calls, stuck loops
    if malformed and (exec_malformed or plan_malformed):
        tool_issues = sum([exec_malformed, plan_malformed])
        fc.primary_category = "tool_use_failure"
        fc.confidence = min(0.9, 0.6 + 0.15 * tool_issues)
        return fc

    # 2. Self-contained task: executor succeeded without planner
    #    Heuristic: no planner turns, or planner was idle (no tool calls)
    #    and executor produced substantial output
    if not has_planner or (len(planner_tool_calls) == 0 and len(exec_tool_calls) > 3):
        if partial < 0.3:
            fc.primary_category = "self_contained_task"
            fc.confidence = 0.65
            return fc

    # 3. Communication failure: planner sent messages but executor didn't follow
    if has_planner and has_messages and follow_rate < 0.25 and len(exec_tool_calls) > 0:
        fc.primary_category = "communication_failure"
        fc.confidence = min(0.85, 0.5 + (0.25 - follow_rate) * 2)
        return fc

    # 4. Verification failure: verifier activity was anomalous
    if has_verifier:
        if false_rejection:
            fc.primary_category = "verification_failure"
            fc.signals["sub_type"] = "false_rejection"
            fc.confidence = 0.75
            return fc
        if missed_bugs:
            fc.primary_category = "verification_failure"
            fc.signals["sub_type"] = "missed_bugs"
            fc.confidence = 0.70
            return fc

    # 5. Specification misinterpretation: planner read spec but spec_coverage
    #    suggests it focused on wrong sections, and the grader failure_modes
    #    indicate a high-level conceptual mismatch
    spec_mismatch_modes = {"wrong_approach", "wrong_algorithm", "misunderstood_spec",
                           "wrong_format", "inverted_logic", "off_by_one_policy"}
    if failure_modes and spec_coverage > 0.5 and any(
        any(kw in fm for kw in ("wrong", "mismatch", "invalid", "format", "approach"))
        for fm in failure_modes
    ):
        fc.primary_category = "specification_misinterpretation"
        fc.confidence = 0.68
        return fc

    # 6. Planning failure: planner had low spec coverage or produced
    #    messages that didn't map to what the task required
    if has_planner and (spec_coverage < 0.4 or len(planner_tool_calls) == 0):
        fc.primary_category = "planning_failure"
        fc.confidence = min(0.80, 0.5 + (0.4 - spec_coverage) * 0.75)
        return fc

    # 7. Execution failure (default for team runs where planner was active
    #    and follow-through was reasonable but task still failed)
    if has_planner and follow_rate >= 0.25 and len(exec_tool_calls) > 0:
        fc.primary_category = "execution_failure"
        fc.confidence = 0.60
        return fc

    # Fallback for single-role runs (oracle/restricted)
    if condition in ("oracle", "restricted"):
        fc.primary_category = "execution_failure"
        fc.confidence = 0.55
        return fc

    fc.primary_category = "unknown"
    fc.confidence = 0.30
    return fc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def classify_run(run_dir: str) -> FailureClassification:
    """Classify a single run directory into a failure category."""
    return _classify_run(run_dir)


def analyze_failures(task_id: str, runs_dir: str) -> TaskFailureReport:
    """
    Analyse all runs for a task and produce an aggregated failure report.

    Args:
        task_id:  Task identifier (e.g. "P1_policy_config").
        runs_dir: Path to directory containing run subdirectories for this
                  task (i.e. shared/ablation_runs/P1_policy_config).

    Returns:
        TaskFailureReport with per-run classifications and aggregate stats.
    """
    report = TaskFailureReport(task_id=task_id, runs_dir=runs_dir)

    if not os.path.isdir(runs_dir):
        return report

    cond_scores: dict[str, list[float]] = defaultdict(list)

    for run_id in sorted(os.listdir(runs_dir)):
        run_path = os.path.join(runs_dir, run_id)
        if not os.path.isdir(run_path):
            continue

        fc = _classify_run(run_path)
        report.classifications.append(fc)
        report.total_runs += 1
        if fc.passed:
            report.passed_runs += 1
        report.category_counts[fc.primary_category] += 1
        cond_scores[fc.condition].append(fc.task_success)

    # Per-condition pass rates
    for cond, scores in cond_scores.items():
        if scores:
            report.condition_pass_rates[cond] = sum(scores) / len(scores)

    # Dominant failure category (exclude "success" and "unknown")
    failure_cats = {
        k: v for k, v in report.category_counts.items()
        if k not in ("success", "unknown")
    }
    if failure_cats:
        report.dominant_failure = max(failure_cats, key=failure_cats.get)

    # Team vs oracle comparison
    oracle_rate = report.condition_pass_rates.get("oracle")
    team_rate = report.condition_pass_rates.get("full", report.condition_pass_rates.get("team"))
    if oracle_rate is not None and team_rate is not None:
        report.team_oracle_delta = team_rate - oracle_rate
        report.team_helps = report.team_oracle_delta > 0.05

    return report


def analyze_failures_across_tasks(
    ablation_runs_dir: str,
    task_ids: list[str] | None = None,
) -> list[TaskFailureReport]:
    """
    Analyse failures for multiple tasks under an ablation_runs directory.

    Args:
        ablation_runs_dir: Root directory containing per-task subdirs.
        task_ids:          Optional filter list; if None, all tasks are analysed.

    Returns:
        List of TaskFailureReport, one per task.
    """
    if not os.path.isdir(ablation_runs_dir):
        return []

    reports: list[TaskFailureReport] = []
    for task_name in sorted(os.listdir(ablation_runs_dir)):
        if task_ids and task_name not in task_ids:
            continue
        task_path = os.path.join(ablation_runs_dir, task_name)
        if not os.path.isdir(task_path):
            continue
        report = analyze_failures(task_name, task_path)
        if report.total_runs > 0:
            reports.append(report)
    return reports


def print_failure_report(report: TaskFailureReport) -> None:
    print(f"\nFailure Analysis: {report.task_id}")
    print("=" * 65)
    print(f"  Runs analysed:    {report.total_runs}")
    print(f"  Passed:           {report.passed_runs}/{report.total_runs}")
    print(f"  Dominant failure: {report.dominant_failure}")
    if report.team_oracle_delta is not None:
        direction = "helps" if report.team_helps else "hurts"
        print(f"  Team vs Oracle:   {report.team_oracle_delta:+.3f} (team {direction})")
    print()

    print("  Category breakdown:")
    for cat, count in sorted(report.category_counts.items(), key=lambda x: -x[1]):
        bar = "#" * count
        print(f"    {cat:<35} {count:2d}  {bar}")

    print()
    print("  Per-condition pass rates:")
    for cond, rate in sorted(report.condition_pass_rates.items()):
        print(f"    {cond:<25} {rate:.3f}")

    print()
    print("  Run details:")
    print(f"  {'Run ID':<28} {'Cond':<12} {'Score':>6} {'Category':<35} {'Conf':>5}")
    print("  " + "-" * 93)
    for fc in report.classifications:
        print(
            f"  {fc.run_id:<28} {fc.condition:<12} {fc.task_success:>6.3f} "
            f"{fc.primary_category:<35} {fc.confidence:>5.2f}"
        )


def print_aggregate_summary(reports: list[TaskFailureReport]) -> None:
    print(f"\nAggregate Failure Analysis ({len(reports)} tasks)")
    print("=" * 65)

    all_cats: Counter = Counter()
    for r in reports:
        all_cats.update(r.category_counts)

    total = sum(all_cats.values())
    print(f"\n  Global category distribution ({total} runs):")
    for cat, count in all_cats.most_common():
        pct = count / max(1, total) * 100
        bar = "#" * max(1, count // max(1, total // 30))
        print(f"    {cat:<35} {count:3d} ({pct:4.1f}%)  {bar}")

    team_helps = sum(1 for r in reports if r.team_helps is True)
    team_hurts = sum(1 for r in reports if r.team_helps is False)
    team_neutral = sum(1 for r in reports if r.team_helps is None)
    print(f"\n  Team coordination effect:")
    print(f"    Helps:   {team_helps}")
    print(f"    Hurts:   {team_hurts}")
    print(f"    Neutral: {team_neutral}")


def main() -> None:
    ap = argparse.ArgumentParser(description="TeamBench failure taxonomy analysis")
    ap.add_argument("--task", default=None, help="Task ID to analyse (e.g. P1_policy_config)")
    ap.add_argument("--runs-dir", default=None,
                    help="Directory with run subdirs for the task "
                         "(defaults to shared/ablation_runs/<task>)")
    ap.add_argument("--run-dir", default=None, help="Classify a single run directory")
    ap.add_argument("--ablation-runs", default=None,
                    help="Analyse all tasks under this ablation_runs root")
    ap.add_argument("--output", default=None, help="Write JSON report to this path")
    args = ap.parse_args()

    if args.run_dir:
        fc = classify_run(args.run_dir)
        print(f"\nRun: {args.run_dir}")
        print(f"  Condition:        {fc.condition}")
        print(f"  Task Success:     {fc.task_success:.3f}")
        print(f"  Passed:           {fc.passed}")
        print(f"  Primary Category: {fc.primary_category}")
        print(f"  Confidence:       {fc.confidence:.2f}")
        print(f"  Grader Failures:  {fc.grader_failure_modes}")
        print(f"  Signals:          {json.dumps(fc.signals, indent=4)}")
        if args.output:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(fc.to_dict(), f, indent=2)
            print(f"\nJSON written to: {args.output}")
        return

    if args.ablation_runs:
        reports = analyze_failures_across_tasks(args.ablation_runs)
        print_aggregate_summary(reports)
        for r in reports:
            print_failure_report(r)
        if args.output:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, "w") as f:
                json.dump([r.to_dict() for r in reports], f, indent=2)
            print(f"\nJSON written to: {args.output}")
        return

    if args.task:
        runs_dir = args.runs_dir
        if not runs_dir:
            # Auto-detect common locations
            for candidate in (
                os.path.join("shared", "ablation_runs", args.task),
                os.path.join("shared", "runs", args.task),
            ):
                if os.path.isdir(candidate):
                    runs_dir = candidate
                    break
        if not runs_dir:
            ap.error(
                f"Could not locate runs for task '{args.task}'. "
                "Use --runs-dir to specify the path."
            )

        report = analyze_failures(args.task, runs_dir)
        print_failure_report(report)

        if args.output:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(report.to_dict(), f, indent=2)
            print(f"\nJSON written to: {args.output}")
        return

    ap.print_help()
    print("\nProvide --task, --run-dir, or --ablation-runs.")


if __name__ == "__main__":
    main()
