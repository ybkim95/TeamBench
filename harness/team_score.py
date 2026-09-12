"""
TeamBench — TeamScore composite metric.

Computes a multi-dimensional score from existing run data without requiring
new experiments.  All sub-metrics are estimated from what is available in
the run directories:

  task_success         — partial_score from grader [0, 1]
  communication_efficiency — useful token density in planner→executor messages
  planning_precision   — fraction of planner turns that include actionable
                         tool-call instructions (proxy for on-target guidance)
  verification_accuracy — did the verifier's tool use reflect genuine checking
                         vs. empty turns (proxy for real bug-catching effort)
  role_consistency     — fraction of tool calls that are permitted for each role
  cost_efficiency      — task_success / (total_tool_calls + 1) as a proxy for
                         effort-adjusted performance (token counts not stored)
  coordination_overhead — ratio of team tool calls vs oracle tool calls for the
                          same task (requires oracle_run_dir)
  composite            — weighted combination

Usage:
    from harness.team_score import compute_team_score
    score = compute_team_score(run_dir, oracle_run_dir=None)

CLI:
    python -m harness.team_score --run-dir PATH [--oracle-run-dir PATH] [--output PATH]
"""
from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Role tool allow-lists (mirrors harness restrictions)
# ---------------------------------------------------------------------------
_PLANNER_ALLOWED = frozenset({
    "read", "list", "ls", "find", "grep", "cat", "head", "tail",
    "bandit", "ruff", "pylint", "mypy", "semgrep", "wc", "python", "python3",
    "message", "send_message",
})
_EXECUTOR_ALLOWED = frozenset({
    "read", "write", "edit", "bash", "run", "python", "python3",
    "list", "ls", "grep", "find", "cat", "head", "tail",
    "message", "send_message",
})
_VERIFIER_ALLOWED = frozenset({
    "read", "bash", "run", "python", "python3", "pytest",
    "list", "ls", "grep", "find", "cat", "head", "tail",
    "message", "send_message",
})

_ROLE_ALLOWED: dict[str, frozenset[str]] = {
    "planner": _PLANNER_ALLOWED,
    "executor": _EXECUTOR_ALLOWED,
    "verifier": _VERIFIER_ALLOWED,
    "oracle": _EXECUTOR_ALLOWED | _PLANNER_ALLOWED | _VERIFIER_ALLOWED,
    "restricted": _EXECUTOR_ALLOWED,
}

# Composite weight vector (must sum to 1.0)
_WEIGHTS: dict[str, float] = {
    "task_success": 0.40,
    "communication_efficiency": 0.10,
    "planning_precision": 0.12,
    "verification_accuracy": 0.12,
    "role_consistency": 0.08,
    "cost_efficiency": 0.18,
}


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------
@dataclass
class TeamScore:
    task_success: float = 0.0
    communication_efficiency: float = 0.0
    planning_precision: float = 0.0
    verification_accuracy: float = 0.0
    role_consistency: float = 0.0
    cost_efficiency: float = 0.0
    coordination_overhead: float | None = None  # None when no oracle run
    composite: float = 0.0

    # Diagnostic counts (not weighted)
    total_messages: int = 0
    total_tool_calls: int = 0
    planner_turns: int = 0
    executor_turns: int = 0
    verifier_turns: int = 0
    condition: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_success": self.task_success,
            "communication_efficiency": self.communication_efficiency,
            "planning_precision": self.planning_precision,
            "verification_accuracy": self.verification_accuracy,
            "role_consistency": self.role_consistency,
            "cost_efficiency": self.cost_efficiency,
            "coordination_overhead": self.coordination_overhead,
            "composite": self.composite,
            "diagnostics": {
                "total_messages": self.total_messages,
                "total_tool_calls": self.total_tool_calls,
                "planner_turns": self.planner_turns,
                "executor_turns": self.executor_turns,
                "verifier_turns": self.verifier_turns,
                "condition": self.condition,
            },
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _load_json(path: str) -> dict:
    """Load a JSON file, returning {} on error."""
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _iter_turn_files(role_dir: str) -> list[str]:
    """Return sorted turn_*.json paths under a role directory (recursive)."""
    paths: list[str] = []
    if not os.path.isdir(role_dir):
        return paths
    for root, _dirs, files in os.walk(role_dir):
        for fn in sorted(files):
            if fn.startswith("turn_") and fn.endswith(".json"):
                paths.append(os.path.join(root, fn))
    return sorted(paths)


def _load_turns(role_dir: str) -> list[dict]:
    turns = []
    for path in _iter_turn_files(role_dir):
        t = _load_json(path)
        if t:
            turns.append(t)
    return turns


def _count_tool_calls(turns: list[dict]) -> int:
    return sum(len(t.get("tool_calls", [])) for t in turns)


def _load_dialogue(run_dir: str) -> list[dict]:
    dlg_path = os.path.join(run_dir, "messages", "dialogue.jsonl")
    messages: list[dict] = []
    if not os.path.isfile(dlg_path):
        return messages
    with open(dlg_path) as f:
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
    """Detect the ablation condition from run_meta or log directories."""
    meta = _load_json(os.path.join(run_dir, "run_meta.json"))
    if "condition" in meta:
        return str(meta["condition"])
    logs = os.path.join(run_dir, "logs")
    for cond in ("oracle", "restricted"):
        if os.path.isdir(os.path.join(logs, cond)):
            return cond
    has_planner = os.path.isdir(os.path.join(logs, "planner"))
    has_executor = os.path.isdir(os.path.join(logs, "executor"))
    has_verifier = os.path.isdir(os.path.join(logs, "verifier"))
    if has_planner or has_executor:
        if has_planner and has_verifier:
            return "full"
        if has_planner:
            return "team_no_verify"
        if has_verifier:
            return "team_no_plan"
        return "full"  # planner+executor, treat as full
    # Check dialogue first role
    msgs = _load_dialogue(run_dir)
    if msgs:
        return msgs[0].get("role", "unknown")
    return "unknown"


def _get_partial_score(run_dir: str) -> float:
    score = _load_json(os.path.join(run_dir, "reports", "score.json"))
    if not score:
        return 0.0
    return float(
        score.get("secondary", {}).get(
            "partial_score", 1.0 if score.get("pass") else 0.0
        )
    )


# ---------------------------------------------------------------------------
# Sub-metric computations
# ---------------------------------------------------------------------------
def _compute_communication_efficiency(messages: list[dict]) -> float:
    """
    Estimate useful information density in planner→executor messages.

    Heuristic: messages that contain structured markers (numbered lists,
    bullet points, code-like segments) are considered "useful".  The ratio
    of useful character volume to total character volume gives efficiency.
    """
    if not messages:
        return 0.0

    planner_msgs = [m for m in messages if m.get("role") == "planner"]
    if not planner_msgs:
        return 0.0

    useful_chars = 0
    total_chars = 0
    for msg in planner_msgs:
        content = str(msg.get("content", ""))
        total_chars += len(content)
        # Proxy for structured/actionable content
        markers = content.count("\n") + content.count("1.") + content.count("- ") + \
                  content.count("```") + content.count("**") + content.count("##")
        # Rough heuristic: structured marker density * content length
        density = min(1.0, markers / max(1, len(content) / 100))
        useful_chars += int(len(content) * (0.5 + 0.5 * density))

    return min(1.0, useful_chars / max(1, total_chars))


def _compute_planning_precision(planner_turns: list[dict]) -> float:
    """
    Fraction of planner turns that include tool calls (i.e., active investigation).

    A planner that reads the spec and produces messages is considered
    precise.  Empty turns that just emit text with no grounding are
    penalised.
    """
    if not planner_turns:
        return 0.0
    active = sum(
        1 for t in planner_turns
        if t.get("tool_calls") or (t.get("text") or "").strip()
    )
    return active / len(planner_turns)


def _compute_verification_accuracy(verifier_turns: list[dict], score: dict) -> float:
    """
    Estimate verifier quality from two signals:

    1. Tool-use activity: a verifier that uses tools (runs checks, reads files)
       is more likely to have caught real bugs.
    2. Outcome alignment: if task passed, the verifier presumably accepted
       correctly; if task failed and failure_modes exist, the verifier may
       have missed them.

    Returns a score in [0, 1].
    """
    if not verifier_turns:
        return 0.5  # no verifier present; neutral

    total = len(verifier_turns)
    active = sum(1 for t in verifier_turns if t.get("tool_calls"))
    activity_score = active / max(1, total)

    passed = bool(score.get("pass"))
    failure_modes = score.get("failure_modes", [])
    has_failures = len(failure_modes) > 0

    if passed:
        # Correct acceptance — good
        outcome_score = 1.0
    elif has_failures and activity_score > 0.5:
        # Verifier was active but task still failed — partial credit
        # (the verifier might have caught issues and triggered remediation)
        outcome_score = 0.6
    elif has_failures and activity_score <= 0.5:
        # Task failed and verifier was mostly idle — likely missed bugs
        outcome_score = 0.2
    else:
        outcome_score = 0.5

    return 0.5 * activity_score + 0.5 * outcome_score


def _compute_role_consistency(
    planner_turns: list[dict],
    executor_turns: list[dict],
    verifier_turns: list[dict],
    oracle_turns: list[dict],
) -> float:
    """
    Fraction of tool calls that are within each role's allowed set.
    Calls to unknown tools are treated as violations.
    """
    pairs: list[tuple[list[dict], str]] = [
        (planner_turns, "planner"),
        (executor_turns, "executor"),
        (verifier_turns, "verifier"),
        (oracle_turns, "oracle"),
    ]
    total_calls = 0
    compliant_calls = 0
    for turns, role in pairs:
        allowed = _ROLE_ALLOWED.get(role, frozenset())
        for turn in turns:
            for tc in turn.get("tool_calls", []):
                tool_name = tc.get("name", "").lower()
                total_calls += 1
                if not tool_name or tool_name in allowed:
                    compliant_calls += 1

    if total_calls == 0:
        return 1.0  # no tool calls → no violations
    return compliant_calls / total_calls


def _compute_cost_efficiency(task_success: float, total_tool_calls: int) -> float:
    """
    task_success per unit effort (tool calls as proxy for cost).
    Normalised to [0, 1] via a soft cap.
    """
    if total_tool_calls == 0:
        return task_success  # no effort, trivial task
    raw = task_success / math.log1p(total_tool_calls)
    # Typical run has ~10-30 tool calls; log(30)≈3.4 → raw ≈ 0.29 for full pass
    # Normalise so ~10 tool calls with full pass ≈ 1.0
    return min(1.0, raw / math.log1p(10))


def _compute_coordination_overhead(
    run_dir: str, oracle_run_dir: str
) -> float | None:
    """
    (team_tool_calls - oracle_tool_calls) / oracle_tool_calls.

    Positive = team used more calls (overhead).
    Negative = team was more efficient.
    Returns None if oracle data is unavailable.
    """
    def _total_calls(rd: str) -> int:
        total = 0
        logs = os.path.join(rd, "logs")
        if not os.path.isdir(logs):
            return 0
        for role in os.listdir(logs):
            role_dir = os.path.join(logs, role)
            turns = _load_turns(role_dir)
            total += _count_tool_calls(turns)
        return total

    oracle_calls = _total_calls(oracle_run_dir)
    if oracle_calls == 0:
        return None
    team_calls = _total_calls(run_dir)
    return (team_calls - oracle_calls) / oracle_calls


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def compute_team_score(
    run_dir: str,
    oracle_run_dir: str | None = None,
) -> TeamScore:
    """
    Compute TeamScore for a single run directory.

    Args:
        run_dir: Path to a run directory (contains logs/, reports/, messages/).
        oracle_run_dir: Optional path to the matched oracle run for the same
                        task; enables coordination_overhead computation.

    Returns:
        TeamScore dataclass with all sub-metrics and composite.
    """
    score_data = _load_json(os.path.join(run_dir, "reports", "score.json"))
    condition = _infer_condition(run_dir)

    # Load turn logs per role
    logs_dir = os.path.join(run_dir, "logs")
    planner_turns = _load_turns(os.path.join(logs_dir, "planner"))
    executor_turns = _load_turns(os.path.join(logs_dir, "executor"))
    oracle_turns = _load_turns(os.path.join(logs_dir, "oracle"))
    restricted_turns = _load_turns(os.path.join(logs_dir, "restricted"))

    # Verifier: may live under logs/verifier/attempt_N/
    verifier_base = os.path.join(logs_dir, "verifier")
    verifier_turns: list[dict] = []
    if os.path.isdir(verifier_base):
        for attempt in sorted(os.listdir(verifier_base)):
            attempt_dir = os.path.join(verifier_base, attempt)
            verifier_turns.extend(_load_turns(attempt_dir))

    messages = _load_dialogue(run_dir)

    # Aggregate tool call counts
    all_turns = planner_turns + executor_turns + verifier_turns + oracle_turns + restricted_turns
    total_tool_calls = _count_tool_calls(all_turns)

    # Sub-metrics
    task_success = _get_partial_score(run_dir)
    comm_eff = _compute_communication_efficiency(messages)
    plan_prec = _compute_planning_precision(planner_turns)
    verify_acc = _compute_verification_accuracy(verifier_turns, score_data)
    role_cons = _compute_role_consistency(
        planner_turns, executor_turns, verifier_turns, oracle_turns
    )
    cost_eff = _compute_cost_efficiency(task_success, total_tool_calls)

    coord_overhead: float | None = None
    if oracle_run_dir and os.path.isdir(oracle_run_dir):
        coord_overhead = _compute_coordination_overhead(run_dir, oracle_run_dir)

    # Weighted composite (coordination_overhead excluded from composite;
    # it is a diagnostic metric, not a quality indicator per se)
    composite = (
        _WEIGHTS["task_success"] * task_success
        + _WEIGHTS["communication_efficiency"] * comm_eff
        + _WEIGHTS["planning_precision"] * plan_prec
        + _WEIGHTS["verification_accuracy"] * verify_acc
        + _WEIGHTS["role_consistency"] * role_cons
        + _WEIGHTS["cost_efficiency"] * cost_eff
    )

    return TeamScore(
        task_success=round(task_success, 4),
        communication_efficiency=round(comm_eff, 4),
        planning_precision=round(plan_prec, 4),
        verification_accuracy=round(verify_acc, 4),
        role_consistency=round(role_cons, 4),
        cost_efficiency=round(cost_eff, 4),
        coordination_overhead=round(coord_overhead, 4) if coord_overhead is not None else None,
        composite=round(composite, 4),
        total_messages=len(messages),
        total_tool_calls=total_tool_calls,
        planner_turns=len(planner_turns),
        executor_turns=len(executor_turns),
        verifier_turns=len(verifier_turns),
        condition=condition,
    )


def compute_team_scores_for_task(task_dir: str) -> list[dict]:
    """
    Compute TeamScore for every run under a task directory.

    Automatically pairs team runs with oracle runs for the same task
    to compute coordination_overhead where possible.

    Returns a list of dicts with run_id and all score fields.
    """
    if not os.path.isdir(task_dir):
        return []

    run_dirs: dict[str, str] = {}  # run_id -> path
    for run_id in sorted(os.listdir(task_dir)):
        run_path = os.path.join(task_dir, run_id)
        if os.path.isdir(run_path):
            run_dirs[run_id] = run_path

    # Find oracle run (for coordination_overhead)
    oracle_run: str | None = None
    for rid, rpath in run_dirs.items():
        if _infer_condition(rpath) == "oracle":
            oracle_run = rpath
            break

    results = []
    for run_id, run_path in run_dirs.items():
        s = compute_team_score(run_path, oracle_run_dir=oracle_run)
        d = s.to_dict()
        d["run_id"] = run_id
        results.append(d)
    return results


def print_score_report(score: TeamScore, run_dir: str) -> None:
    print(f"\nTeamScore Report: {run_dir}")
    print("=" * 60)
    print(f"  Condition:               {score.condition}")
    print(f"  Task Success:            {score.task_success:.4f}")
    print(f"  Communication Efficiency:{score.communication_efficiency:.4f}")
    print(f"  Planning Precision:      {score.planning_precision:.4f}")
    print(f"  Verification Accuracy:   {score.verification_accuracy:.4f}")
    print(f"  Role Consistency:        {score.role_consistency:.4f}")
    print(f"  Cost Efficiency:         {score.cost_efficiency:.4f}")
    if score.coordination_overhead is not None:
        print(f"  Coordination Overhead:   {score.coordination_overhead:+.4f}")
    print(f"  Composite:               {score.composite:.4f}")
    print("-" * 60)
    print(f"  Tool Calls (total):      {score.total_tool_calls}")
    print(f"  Messages (dialogue):     {score.total_messages}")
    print(f"  Planner Turns:           {score.planner_turns}")
    print(f"  Executor Turns:          {score.executor_turns}")
    print(f"  Verifier Turns:          {score.verifier_turns}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Compute TeamBench TeamScore composite metric")
    ap.add_argument("--run-dir", required=True, help="Path to a single run directory")
    ap.add_argument("--oracle-run-dir", default=None, help="Matched oracle run directory")
    ap.add_argument("--output", default=None, help="Write JSON result to this path")
    args = ap.parse_args()

    score = compute_team_score(args.run_dir, oracle_run_dir=args.oracle_run_dir)
    print_score_report(score, args.run_dir)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(score.to_dict(), f, indent=2)
        print(f"\nJSON result written to: {args.output}")


if __name__ == "__main__":
    main()
