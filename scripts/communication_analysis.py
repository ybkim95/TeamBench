#!/usr/bin/env python3
"""
TeamBench communication/message pattern analysis.

Analyses agent communication patterns from ablation run directories, including
message volumes, efficiency correlations, remediation loops, failure taxonomy,
and turn patterns.

Data sources:
  shared/ablation_results/ablation_runs/*/   — run directories
    messages/dialogue.jsonl                  — inter-agent messages
    logs/{role}/turn_*.json                  — per-turn execution logs
    run_meta.json                            — condition/task/seed
    reports/score.json                       — pass/partial_score/failure_modes
  shared/ablation_results/*.json             — ablation result files with runs list

Outputs:
  shared/paper/communication_analysis.json  — full results
  shared/paper/table_communication.tex      — LaTeX summary table

Usage:
    python scripts/communication_analysis.py [--runs-dir PATH] [--output-dir PATH]
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RUNS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "shared", "ablation_results", "ablation_runs",
)
OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "shared", "paper",
)
CHARS_PER_TOKEN = 4  # rough estimate for token counting

# Conditions that involve planner/verifier roles
TEAM_CONDITIONS = {"full", "team_no_verify", "team_no_plan"}
ALL_CONDITIONS = {"oracle", "restricted", "full", "team_no_verify", "team_no_plan"}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RunData:
    run_id: str
    task_id: str
    seed: int
    condition: str
    run_dir: str
    # Score fields
    score: float = 0.0
    passed: bool = False
    failure_modes: list[str] = field(default_factory=list)
    # Message fields (from dialogue.jsonl)
    messages: list[dict] = field(default_factory=list)
    # Turn fields (from logs/)
    turns_by_role: dict[str, list[dict]] = field(default_factory=dict)

    @property
    def has_dialogue(self) -> bool:
        return len(self.messages) > 0

    @property
    def has_turns(self) -> bool:
        return len(self.turns_by_role) > 0


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_run(run_dir: str) -> Optional[RunData]:
    """Load a single run directory. Returns None if run_meta.json is missing."""
    meta_path = os.path.join(run_dir, "run_meta.json")
    if not os.path.exists(meta_path):
        return None
    try:
        meta = json.loads(open(meta_path).read())
    except Exception:
        return None

    task_id = meta.get("task_id", "")
    run_id = meta.get("run_id", os.path.basename(run_dir))
    seed = meta.get("seed", 0)
    condition = meta.get("condition", "")

    run = RunData(
        run_id=run_id,
        task_id=task_id,
        seed=seed,
        condition=condition,
        run_dir=run_dir,
    )

    # Load score
    score_path = os.path.join(run_dir, "reports", "score.json")
    if os.path.exists(score_path):
        try:
            score_data = json.loads(open(score_path).read())
            run.score = float(score_data.get("score", score_data.get("partial_score", 0.0)))
            run.passed = bool(score_data.get("pass", score_data.get("passed_bool", False)))
            run.failure_modes = score_data.get("failure_modes", [])
        except Exception:
            pass

    # Load dialogue
    dialogue_path = os.path.join(run_dir, "messages", "dialogue.jsonl")
    if os.path.exists(dialogue_path):
        try:
            msgs = []
            for line in open(dialogue_path):
                line = line.strip()
                if line:
                    msgs.append(json.loads(line))
            run.messages = msgs
        except Exception:
            pass

    # Load turn logs
    logs_dir = os.path.join(run_dir, "logs")
    if os.path.isdir(logs_dir):
        for role_dir in os.listdir(logs_dir):
            role_path = os.path.join(logs_dir, role_dir)
            if not os.path.isdir(role_path):
                continue
            turns = []
            for turn_file in sorted(glob.glob(os.path.join(role_path, "turn_*.json"))):
                try:
                    turns.append(json.loads(open(turn_file).read()))
                except Exception:
                    pass
            if turns:
                run.turns_by_role[role_dir] = turns

    return run


def load_all_runs(runs_dir: str) -> list[RunData]:
    """Walk runs_dir recursively to find all run directories."""
    runs = []
    # Pattern: runs_dir/<task_or_date>/<run_id>/run_meta.json
    for meta_path in glob.glob(os.path.join(runs_dir, "*", "*", "run_meta.json")):
        run_dir = os.path.dirname(meta_path)
        run = load_run(run_dir)
        if run is not None:
            runs.append(run)
    return runs


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def safe_pearson(xs: list[float], ys: list[float]) -> dict:
    n = len(xs)
    if n < 3:
        return {"r": None, "p": None, "n": n}
    if HAS_SCIPY:
        r, p = scipy_stats.pearsonr(xs, ys)
        return {"r": round(float(r), 4), "p": round(float(p), 4), "n": n}
    # Manual Pearson
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return {"r": None, "p": None, "n": n}
    return {"r": round(num / (dx * dy), 4), "p": None, "n": n}


def safe_spearman(xs: list[float], ys: list[float]) -> dict:
    n = len(xs)
    if n < 3:
        return {"rho": None, "p": None, "n": n}
    if HAS_SCIPY:
        rho, p = scipy_stats.spearmanr(xs, ys)
        return {"rho": round(float(rho), 4), "p": round(float(p), 4), "n": n}
    # Rank-based Pearson fallback
    def ranks(lst):
        sorted_idx = sorted(range(len(lst)), key=lambda i: lst[i])
        r = [0.0] * len(lst)
        for rank, idx in enumerate(sorted_idx):
            r[idx] = float(rank + 1)
        return r
    rx, ry = ranks(xs), ranks(ys)
    return {**safe_pearson(rx, ry), "rho": safe_pearson(rx, ry).get("r"), "p": safe_pearson(rx, ry).get("p"), "n": n}


def quartile_bins(values: list[float]) -> list[float]:
    """Return [Q0, Q1, Q2, Q3, Q4] boundaries."""
    s = sorted(values)
    n = len(s)
    if n < 4:
        return []
    qs = []
    for q in [0, 0.25, 0.5, 0.75, 1.0]:
        idx = q * (n - 1)
        lo, hi = int(idx), min(int(idx) + 1, n - 1)
        frac = idx - lo
        qs.append(s[lo] + frac * (s[hi] - s[lo]))
    return qs


# ---------------------------------------------------------------------------
# 1. Message Volume Analysis
# ---------------------------------------------------------------------------

def analyze_message_volume(runs: list[RunData]) -> dict:
    """Messages per role per condition, avg length, distribution."""
    # {condition: {role: [msg_lengths]}}
    cond_role_lengths: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    # per-run total message counts for distribution
    run_msg_counts: list[int] = []

    for run in runs:
        if not run.has_dialogue:
            continue
        total = 0
        for msg in run.messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "") or ""
            length = len(content)
            cond_role_lengths[run.condition][role].append(length)
            total += 1
        run_msg_counts.append(total)

    results: dict[str, Any] = {}
    for cond, role_map in sorted(cond_role_lengths.items()):
        results[cond] = {}
        for role, lengths in sorted(role_map.items()):
            n = len(lengths)
            avg_chars = sum(lengths) / n if n else 0
            results[cond][role] = {
                "n_messages": n,
                "avg_chars": round(avg_chars, 1),
                "avg_tokens": round(avg_chars / CHARS_PER_TOKEN, 1),
                "total_chars": sum(lengths),
                "total_tokens": round(sum(lengths) / CHARS_PER_TOKEN),
            }

    # Distribution stats
    dist: dict[str, Any] = {}
    if run_msg_counts:
        dist = {
            "n_runs_with_dialogue": len(run_msg_counts),
            "mean": round(sum(run_msg_counts) / len(run_msg_counts), 1),
            "min": min(run_msg_counts),
            "max": max(run_msg_counts),
            "p25": sorted(run_msg_counts)[len(run_msg_counts) // 4],
            "p50": sorted(run_msg_counts)[len(run_msg_counts) // 2],
            "p75": sorted(run_msg_counts)[3 * len(run_msg_counts) // 4],
        }

    return {"by_condition_role": results, "run_message_count_distribution": dist}


# ---------------------------------------------------------------------------
# 2. Communication Efficiency
# ---------------------------------------------------------------------------

def analyze_communication_efficiency(runs: list[RunData]) -> dict:
    """Correlate planner message length and total message count vs score."""
    planner_lengths: list[float] = []
    planner_scores: list[float] = []
    total_count_list: list[float] = []
    count_scores: list[float] = []

    for run in runs:
        if not run.has_dialogue:
            continue
        planner_msgs = [m for m in run.messages if m.get("role") == "planner"]
        planner_total = sum(len(m.get("content", "") or "") for m in planner_msgs)
        total_count = len(run.messages)

        if planner_total > 0:
            planner_lengths.append(float(planner_total))
            planner_scores.append(run.score)

        total_count_list.append(float(total_count))
        count_scores.append(run.score)

    # Quartile analysis: bin runs by planner message length
    quartile_analysis: dict[str, Any] = {}
    if len(planner_lengths) >= 4:
        bounds = quartile_bins(planner_lengths)
        if bounds:
            bins = [[], [], [], []]
            for length, score in zip(planner_lengths, planner_scores):
                if length <= bounds[1]:
                    bins[0].append(score)
                elif length <= bounds[2]:
                    bins[1].append(score)
                elif length <= bounds[3]:
                    bins[2].append(score)
                else:
                    bins[3].append(score)
            labels = ["Q1 (short)", "Q2", "Q3", "Q4 (long)"]
            for label, bin_scores in zip(labels, bins):
                if bin_scores:
                    quartile_analysis[label] = {
                        "n": len(bin_scores),
                        "mean_score": round(sum(bin_scores) / len(bin_scores), 4),
                        "pass_rate": round(sum(1 for s in bin_scores if s >= 1.0) / len(bin_scores), 4),
                    }

    return {
        "planner_length_vs_score": {
            "pearson": safe_pearson(planner_lengths, planner_scores),
            "spearman": safe_spearman(planner_lengths, planner_scores),
        },
        "message_count_vs_score": {
            "pearson": safe_pearson(total_count_list, count_scores),
            "spearman": safe_spearman(total_count_list, count_scores),
        },
        "optimal_length_by_quartile": quartile_analysis,
    }


# ---------------------------------------------------------------------------
# 3. Remediation Loop Analysis
# ---------------------------------------------------------------------------

def analyze_remediation_loops(runs: list[RunData]) -> dict:
    """
    Count verifier->executor feedback loops.
    A remediation loop = verifier sends a message to executor (rejection/feedback).
    """
    runs_with_remediation: list[RunData] = []
    runs_without_remediation: list[RunData] = []
    remediation_counts: list[int] = []

    for run in runs:
        if not run.has_dialogue:
            continue

        # Count verifier->executor messages (feedback/rejection signals)
        feedback_count = sum(
            1 for m in run.messages
            if m.get("role") == "verifier" and m.get("to") == "executor"
        )
        # Also count verifier->planner as remediation escalation
        escalation_count = sum(
            1 for m in run.messages
            if m.get("role") == "verifier" and m.get("to") == "planner"
        )
        total_remediation = feedback_count + escalation_count

        if total_remediation > 0:
            runs_with_remediation.append(run)
        else:
            runs_without_remediation.append(run)
        remediation_counts.append(total_remediation)

    def mean_score(rlist: list[RunData]) -> Optional[float]:
        if not rlist:
            return None
        return round(sum(r.score for r in rlist) / len(rlist), 4)

    def pass_rate(rlist: list[RunData]) -> Optional[float]:
        if not rlist:
            return None
        return round(sum(1 for r in rlist if r.passed) / len(rlist), 4)

    avg_rounds = (
        round(sum(remediation_counts) / len(remediation_counts), 2)
        if remediation_counts else 0.0
    )

    return {
        "n_runs_with_dialogue": len(remediation_counts),
        "n_runs_with_remediation": len(runs_with_remediation),
        "n_runs_without_remediation": len(runs_without_remediation),
        "avg_remediation_rounds": avg_rounds,
        "success_rate_with_remediation": {
            "mean_score": mean_score(runs_with_remediation),
            "pass_rate": pass_rate(runs_with_remediation),
            "n": len(runs_with_remediation),
        },
        "success_rate_without_remediation": {
            "mean_score": mean_score(runs_without_remediation),
            "pass_rate": pass_rate(runs_without_remediation),
            "n": len(runs_without_remediation),
        },
    }


# ---------------------------------------------------------------------------
# 4. Communication Failure Taxonomy
# ---------------------------------------------------------------------------

def analyze_failure_taxonomy(runs: list[RunData]) -> dict:
    """
    Classify runs by communication failure patterns:
      - silent_planner: planner in team condition but no/minimal message (<50 chars)
      - ignored_plan: planner sends long plan but executor score is low
      - false_rejection: verifier rejects but task would pass (score after verification low)
      - effective_relay: planner message leads to high score
    """
    silent_planner: list[RunData] = []
    ignored_plan: list[RunData] = []
    false_rejection_proxy: list[RunData] = []
    effective_relay: list[RunData] = []

    SILENT_THRESHOLD = 50    # chars
    LONG_PLAN_THRESHOLD = 500  # chars — planner actually sent a plan
    HIGH_SCORE = 0.8
    LOW_SCORE = 0.3

    for run in runs:
        if run.condition not in TEAM_CONDITIONS:
            continue

        planner_msgs = [m for m in run.messages if m.get("role") == "planner"]
        planner_total_chars = sum(len(m.get("content", "") or "") for m in planner_msgs)
        verifier_msgs = [m for m in run.messages if m.get("role") == "verifier"]

        # Silent planner: team condition, but planner sends nothing or minimal text
        if run.condition in {"full", "team_no_verify"}:
            if planner_total_chars < SILENT_THRESHOLD:
                silent_planner.append(run)

        # Ignored plan: planner sent substantial plan, but score is low
        if planner_total_chars >= LONG_PLAN_THRESHOLD and run.score < LOW_SCORE:
            ignored_plan.append(run)

        # False rejection proxy: verifier sends feedback but score ends up low
        # (verifier rejected work that the grader also scored low — not actually false,
        #  but captures cases where verifier introduced overhead without helping)
        verifier_feedback = [
            m for m in verifier_msgs if m.get("to") in ("executor", "planner")
        ]
        if verifier_feedback and run.score < LOW_SCORE:
            false_rejection_proxy.append(run)

        # Effective relay: planner sent plan AND score is high
        if planner_total_chars >= LONG_PLAN_THRESHOLD and run.score >= HIGH_SCORE:
            effective_relay.append(run)

    def stats(rlist: list[RunData]) -> dict:
        n = len(rlist)
        if n == 0:
            return {"n": 0, "mean_score": None, "pass_rate": None}
        return {
            "n": n,
            "mean_score": round(sum(r.score for r in rlist) / n, 4),
            "pass_rate": round(sum(1 for r in rlist if r.passed) / n, 4),
        }

    # Count team-condition runs for base rates
    team_runs = [r for r in runs if r.condition in TEAM_CONDITIONS and r.has_dialogue]

    return {
        "n_team_runs_with_dialogue": len(team_runs),
        "silent_planner": {
            **stats(silent_planner),
            "description": "Team condition run where planner sends <50 chars total",
        },
        "ignored_plan": {
            **stats(ignored_plan),
            "description": "Planner sends >500 chars but task scores <0.3",
        },
        "false_rejection_proxy": {
            **stats(false_rejection_proxy),
            "description": "Verifier sends feedback to executor/planner but run scores <0.3",
        },
        "effective_relay": {
            **stats(effective_relay),
            "description": "Planner sends >500 chars and task scores >=0.8",
        },
    }


# ---------------------------------------------------------------------------
# 5. Turn Pattern Analysis
# ---------------------------------------------------------------------------

def analyze_turn_patterns(runs: list[RunData]) -> dict:
    """Average turns per role per condition, correlation with success."""
    # {condition: {role: [turn_counts]}}
    cond_role_turns: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    # For correlation: total turns vs score
    total_turns_list: list[float] = []
    turn_scores: list[float] = []

    for run in runs:
        if not run.has_turns:
            continue
        total_turns = 0
        for role, turns in run.turns_by_role.items():
            n_turns = len(turns)
            cond_role_turns[run.condition][role].append(n_turns)
            total_turns += n_turns
        total_turns_list.append(float(total_turns))
        turn_scores.append(run.score)

    results: dict[str, Any] = {}
    for cond, role_map in sorted(cond_role_turns.items()):
        results[cond] = {}
        for role, counts in sorted(role_map.items()):
            n = len(counts)
            results[cond][role] = {
                "n_runs": n,
                "avg_turns": round(sum(counts) / n, 2) if n else 0,
                "min_turns": min(counts) if counts else 0,
                "max_turns": max(counts) if counts else 0,
            }

    # Which role uses most turns overall?
    role_totals: dict[str, int] = defaultdict(int)
    role_run_counts: dict[str, int] = defaultdict(int)
    for run in runs:
        for role, turns in run.turns_by_role.items():
            role_totals[role] += len(turns)
            role_run_counts[role] += 1
    role_avg = {
        role: round(role_totals[role] / role_run_counts[role], 2)
        for role in role_totals
    }
    most_turns_role = max(role_avg, key=role_avg.get) if role_avg else None

    return {
        "by_condition_role": results,
        "turn_count_vs_score": {
            "pearson": safe_pearson(total_turns_list, turn_scores),
            "spearman": safe_spearman(total_turns_list, turn_scores),
        },
        "avg_turns_by_role_overall": role_avg,
        "most_turns_role": most_turns_role,
    }


# ---------------------------------------------------------------------------
# 6. Key Paper Statistics
# ---------------------------------------------------------------------------

def compute_paper_stats(
    runs: list[RunData],
    volume: dict,
    efficiency: dict,
    remediation: dict,
    taxonomy: dict,
    turns: dict,
) -> dict:
    """
    CEI = planning_value / planner_tokens
    Active communication rate
    Team-helps vs team-hurts communication comparison
    """
    # Compute planning_value: full_score - team_no_plan_score per task
    # Group by (task_id, seed)
    by_task_seed: dict[tuple, dict[str, RunData]] = defaultdict(dict)
    for run in runs:
        key = (run.task_id, run.seed)
        by_task_seed[key][run.condition] = run

    planning_values: list[float] = []
    planner_tokens_list: list[float] = []

    for (task_id, seed), cond_map in by_task_seed.items():
        full_run = cond_map.get("full")
        no_plan_run = cond_map.get("team_no_plan")
        if full_run is None or no_plan_run is None:
            continue
        planning_value = full_run.score - no_plan_run.score

        # Planner tokens from full run dialogue
        if full_run.has_dialogue:
            planner_chars = sum(
                len(m.get("content", "") or "")
                for m in full_run.messages
                if m.get("role") == "planner"
            )
            planner_tokens = planner_chars / CHARS_PER_TOKEN
            if planner_tokens > 0:
                planning_values.append(planning_value)
                planner_tokens_list.append(planner_tokens)

    # CEI = mean(planning_value / planner_tokens * 1000)  scaled per 1k tokens
    cei_values = [
        pv / pt * 1000
        for pv, pt in zip(planning_values, planner_tokens_list)
        if pt > 0
    ]
    cei = round(sum(cei_values) / len(cei_values), 6) if cei_values else None

    # Active communication rate: % of team runs where planner sends >50 chars
    team_runs_with_dialogue = [
        r for r in runs if r.condition in TEAM_CONDITIONS and r.has_dialogue
    ]
    active_count = sum(
        1 for r in team_runs_with_dialogue
        if sum(len(m.get("content", "") or "") for m in r.messages if m.get("role") == "planner") > 50
    )
    active_rate = (
        round(active_count / len(team_runs_with_dialogue), 4)
        if team_runs_with_dialogue else None
    )

    # Team-helps vs team-hurts communication patterns
    # Need to identify which tasks are "team-helps" vs "team-hurts"
    # team-helps: full > oracle; team-hurts: full < oracle
    team_helps_runs: list[RunData] = []
    team_hurts_runs: list[RunData] = []

    for (task_id, seed), cond_map in by_task_seed.items():
        full_run = cond_map.get("full")
        oracle_run = cond_map.get("oracle")
        if full_run is None or oracle_run is None:
            continue
        if full_run.score > oracle_run.score:
            team_helps_runs.append(full_run)
        elif full_run.score < oracle_run.score:
            team_hurts_runs.append(full_run)

    def comm_stats(rlist: list[RunData]) -> dict:
        n = len(rlist)
        if n == 0:
            return {"n": 0}
        runs_with_d = [r for r in rlist if r.has_dialogue]
        planner_chars_list = [
            sum(len(m.get("content", "") or "") for m in r.messages if m.get("role") == "planner")
            for r in runs_with_d
        ]
        msg_counts = [len(r.messages) for r in runs_with_d]
        return {
            "n": n,
            "n_with_dialogue": len(runs_with_d),
            "mean_score": round(sum(r.score for r in rlist) / n, 4),
            "avg_planner_chars": round(sum(planner_chars_list) / len(planner_chars_list), 1) if planner_chars_list else None,
            "avg_msg_count": round(sum(msg_counts) / len(msg_counts), 1) if msg_counts else None,
        }

    return {
        "cei": {
            "value": cei,
            "description": "Communication Efficiency Index = planning_value / planner_tokens * 1000",
            "n_pairs": len(cei_values),
        },
        "active_communication_rate": {
            "rate": active_rate,
            "n_team_runs_with_dialogue": len(team_runs_with_dialogue),
            "n_active": active_count,
        },
        "team_helps_communication": comm_stats(team_helps_runs),
        "team_hurts_communication": comm_stats(team_hurts_runs),
    }


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def fmt(v: Any, decimals: int = 4) -> str:
    if v is None:
        return "N/A"
    if isinstance(v, float):
        return f"{v:.{decimals}f}"
    return str(v)


def print_report(
    runs: list[RunData],
    volume: dict,
    efficiency: dict,
    remediation: dict,
    taxonomy: dict,
    turns: dict,
    paper: dict,
) -> None:
    total = len(runs)
    with_dialogue = sum(1 for r in runs if r.has_dialogue)
    with_turns = sum(1 for r in runs if r.has_turns)
    with_score = sum(1 for r in runs if r.score > 0 or r.passed)

    print("=" * 70)
    print("TeamBench Communication Pattern Analysis")
    print("=" * 70)
    print(f"\nData Summary:")
    print(f"  Total runs loaded:        {total}")
    print(f"  Runs with dialogue.jsonl: {with_dialogue}")
    print(f"  Runs with turn logs:      {with_turns}")
    print(f"  Runs with score.json:     {with_score}")

    print("\n" + "-" * 70)
    print("1. MESSAGE VOLUME BY CONDITION AND ROLE")
    print("-" * 70)
    for cond, role_map in sorted(volume["by_condition_role"].items()):
        print(f"\n  Condition: {cond}")
        for role, stats in sorted(role_map.items()):
            print(f"    {role:12s}  msgs={stats['n_messages']:6d}  "
                  f"avg_chars={stats['avg_chars']:8.1f}  "
                  f"avg_tokens={stats['avg_tokens']:7.1f}  "
                  f"total_tokens={stats['total_tokens']:8d}")
    dist = volume.get("run_message_count_distribution", {})
    if dist:
        print(f"\n  Message count per run: mean={dist['mean']}  "
              f"p25={dist['p25']}  p50={dist['p50']}  p75={dist['p75']}  "
              f"max={dist['max']}  (n={dist['n_runs_with_dialogue']})")

    print("\n" + "-" * 70)
    print("2. COMMUNICATION EFFICIENCY CORRELATIONS")
    print("-" * 70)
    pl = efficiency["planner_length_vs_score"]
    print(f"\n  Planner msg length vs score:")
    print(f"    Pearson  r={fmt(pl['pearson']['r'])}  p={fmt(pl['pearson']['p'])}  n={pl['pearson']['n']}")
    print(f"    Spearman rho={fmt(pl['spearman'].get('rho'))}  p={fmt(pl['spearman'].get('p'))}  n={pl['spearman']['n']}")
    mc = efficiency["message_count_vs_score"]
    print(f"\n  Total message count vs score:")
    print(f"    Pearson  r={fmt(mc['pearson']['r'])}  p={fmt(mc['pearson']['p'])}  n={mc['pearson']['n']}")
    print(f"    Spearman rho={fmt(mc['spearman'].get('rho'))}  p={fmt(mc['spearman'].get('p'))}  n={mc['spearman']['n']}")
    print(f"\n  Optimal length by quartile (planner msg length):")
    for q, qstats in efficiency.get("optimal_length_by_quartile", {}).items():
        print(f"    {q:14s}  n={qstats['n']:5d}  "
              f"mean_score={qstats['mean_score']:.4f}  "
              f"pass_rate={qstats['pass_rate']:.4f}")

    print("\n" + "-" * 70)
    print("3. REMEDIATION LOOP ANALYSIS")
    print("-" * 70)
    r = remediation
    print(f"\n  Runs with dialogue:           {r['n_runs_with_dialogue']}")
    print(f"  Runs WITH remediation:        {r['n_runs_with_remediation']}")
    print(f"  Runs WITHOUT remediation:     {r['n_runs_without_remediation']}")
    print(f"  Avg remediation rounds:       {r['avg_remediation_rounds']}")
    wr = r["success_rate_with_remediation"]
    wor = r["success_rate_without_remediation"]
    print(f"\n  WITH remediation    (n={wr['n']:5d}):  mean_score={fmt(wr['mean_score'])}  pass_rate={fmt(wr['pass_rate'])}")
    print(f"  WITHOUT remediation (n={wor['n']:5d}):  mean_score={fmt(wor['mean_score'])}  pass_rate={fmt(wor['pass_rate'])}")

    print("\n" + "-" * 70)
    print("4. COMMUNICATION FAILURE TAXONOMY")
    print("-" * 70)
    t = taxonomy
    print(f"\n  Team runs with dialogue: {t['n_team_runs_with_dialogue']}")
    for key in ["silent_planner", "ignored_plan", "false_rejection_proxy", "effective_relay"]:
        s = t[key]
        print(f"\n  {key.upper()} (n={s['n']}):")
        print(f"    {s['description']}")
        print(f"    mean_score={fmt(s['mean_score'])}  pass_rate={fmt(s['pass_rate'])}")

    print("\n" + "-" * 70)
    print("5. TURN PATTERN ANALYSIS")
    print("-" * 70)
    print(f"\n  Role with most avg turns: {turns.get('most_turns_role', 'N/A')}")
    print(f"\n  Overall avg turns by role:")
    for role, avg in sorted(turns.get("avg_turns_by_role_overall", {}).items()):
        print(f"    {role:12s}  avg_turns={avg}")
    tc = turns.get("turn_count_vs_score", {})
    if tc:
        p = tc.get("pearson", {})
        s = tc.get("spearman", {})
        print(f"\n  Turn count vs score:")
        print(f"    Pearson  r={fmt(p.get('r'))}  p={fmt(p.get('p'))}  n={p.get('n')}")
        print(f"    Spearman rho={fmt(s.get('rho'))}  p={fmt(s.get('p'))}  n={s.get('n')}")
    print(f"\n  Avg turns per role per condition:")
    for cond, role_map in sorted(turns.get("by_condition_role", {}).items()):
        parts = [f"{role}={stats['avg_turns']}" for role, stats in sorted(role_map.items())]
        print(f"    {cond:20s}  {', '.join(parts)}")

    print("\n" + "-" * 70)
    print("6. KEY PAPER STATISTICS")
    print("-" * 70)
    cei = paper["cei"]
    act = paper["active_communication_rate"]
    th = paper["team_helps_communication"]
    thu = paper["team_hurts_communication"]
    print(f"\n  CEI (Communication Efficiency Index):")
    print(f"    {cei['description']}")
    print(f"    value={fmt(cei['value'], 6)}  n_pairs={cei['n_pairs']}")
    print(f"\n  Active communication rate: {fmt(act['rate'])} "
          f"({act['n_active']}/{act['n_team_runs_with_dialogue']} team runs with planner>50 chars)")
    print(f"\n  Team-HELPS runs (full > oracle):")
    print(f"    n={th['n']}  mean_score={fmt(th.get('mean_score'))}  "
          f"avg_planner_chars={fmt(th.get('avg_planner_chars'), 1)}  "
          f"avg_msg_count={fmt(th.get('avg_msg_count'), 1)}")
    print(f"\n  Team-HURTS runs (full < oracle):")
    print(f"    n={thu['n']}  mean_score={fmt(thu.get('mean_score'))}  "
          f"avg_planner_chars={fmt(thu.get('avg_planner_chars'), 1)}  "
          f"avg_msg_count={fmt(thu.get('avg_msg_count'), 1)}")
    print("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# LaTeX table
# ---------------------------------------------------------------------------

def generate_latex_table(volume: dict, efficiency: dict, remediation: dict, paper: dict) -> str:
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Communication Pattern Analysis. Message volumes, efficiency correlations,",
        r"         and key metrics across ablation conditions.",
        r"         Tokens estimated at 4 chars/token.}",
        r"\label{tab:communication}",
        r"\small",
        r"\begin{tabular}{llrrr}",
        r"\toprule",
        r"\textbf{Condition} & \textbf{Role} & \textbf{N msgs} & \textbf{Avg tokens} & \textbf{Total tokens} \\",
        r"\midrule",
    ]

    for cond, role_map in sorted(volume["by_condition_role"].items()):
        first = True
        for role, stats in sorted(role_map.items()):
            cond_str = cond if first else ""
            lines.append(
                f"  {cond_str} & {role} & {stats['n_messages']:,} & "
                f"{stats['avg_tokens']:,.0f} & {stats['total_tokens']:,} \\\\"
            )
            first = False
        lines.append(r"  \midrule")

    lines += [
        r"\end{tabular}",
        r"",
        r"\vspace{4pt}",
        r"\begin{tabular}{lcc}",
        r"\toprule",
        r"\textbf{Metric} & \textbf{Pearson $r$} & \textbf{Spearman $\rho$} \\",
        r"\midrule",
    ]

    pl = efficiency["planner_length_vs_score"]
    mc = efficiency["message_count_vs_score"]
    pr = pl["pearson"]["r"]
    ps = pl["spearman"].get("rho")
    mr = mc["pearson"]["r"]
    ms = mc["spearman"].get("rho")
    lines.append(
        f"  Planner length vs.\ score & "
        f"{'N/A' if pr is None else f'{pr:.3f}'} & "
        f"{'N/A' if ps is None else f'{ps:.3f}'} \\\\"
    )
    lines.append(
        f"  Message count vs.\ score & "
        f"{'N/A' if mr is None else f'{mr:.3f}'} & "
        f"{'N/A' if ms is None else f'{ms:.3f}'} \\\\"
    )
    lines += [r"\midrule"]

    # Remediation row
    r = remediation
    wr = r["success_rate_with_remediation"]
    wor = r["success_rate_without_remediation"]
    ws = fmt(wr["mean_score"]) if wr["mean_score"] is not None else "N/A"
    wos = fmt(wor["mean_score"]) if wor["mean_score"] is not None else "N/A"
    lines.append(
        f"  Mean score w/ remediation ($n={wr['n']}$) & \\multicolumn{{2}}{{c}}{{{ws}}} \\\\"
    )
    lines.append(
        f"  Mean score w/o remediation ($n={wor['n']}$) & \\multicolumn{{2}}{{c}}{{{wos}}} \\\\"
    )
    lines += [r"\midrule"]

    # CEI and active communication
    cei = paper["cei"]
    act = paper["active_communication_rate"]
    cei_val = fmt(cei["value"], 6) if cei["value"] is not None else "N/A"
    act_val = fmt(act["rate"]) if act["rate"] is not None else "N/A"
    lines.append(
        f"  CEI ($n={cei['n_pairs']}$ task pairs) & \\multicolumn{{2}}{{c}}{{{cei_val}}} \\\\"
    )
    lines.append(
        f"  Active comm.\ rate & \\multicolumn{{2}}{{c}}{{{act_val}}} \\\\"
    )

    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="TeamBench communication pattern analysis")
    parser.add_argument(
        "--runs-dir",
        default=RUNS_DIR,
        help="Path to ablation_runs directory",
    )
    parser.add_argument(
        "--output-dir",
        default=OUTPUT_DIR,
        help="Directory for output files",
    )
    args = parser.parse_args()

    print(f"Loading runs from: {args.runs_dir}")
    runs = load_all_runs(args.runs_dir)
    print(f"Loaded {len(runs)} runs")

    # Filter runs that have at least a task_id and condition
    valid_runs = [r for r in runs if r.task_id and r.condition]
    print(f"Valid runs (non-empty task_id + condition): {len(valid_runs)}")

    print("Running analyses...")
    volume = analyze_message_volume(valid_runs)
    efficiency = analyze_communication_efficiency(valid_runs)
    remediation = analyze_remediation_loops(valid_runs)
    taxonomy = analyze_failure_taxonomy(valid_runs)
    turns = analyze_turn_patterns(valid_runs)
    paper = compute_paper_stats(valid_runs, volume, efficiency, remediation, taxonomy, turns)

    print_report(valid_runs, volume, efficiency, remediation, taxonomy, turns, paper)

    # Build output JSON
    import datetime
    output = {
        "generated": datetime.datetime.utcnow().isoformat() + "Z",
        "description": "TeamBench communication pattern analysis",
        "data_summary": {
            "total_runs": len(runs),
            "valid_runs": len(valid_runs),
            "runs_with_dialogue": sum(1 for r in valid_runs if r.has_dialogue),
            "runs_with_turns": sum(1 for r in valid_runs if r.has_turns),
        },
        "message_volume": volume,
        "communication_efficiency": efficiency,
        "remediation_loops": remediation,
        "failure_taxonomy": taxonomy,
        "turn_patterns": turns,
        "paper_stats": paper,
    }

    os.makedirs(args.output_dir, exist_ok=True)
    json_path = os.path.join(args.output_dir, "communication_analysis.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved JSON: {json_path}")

    latex = generate_latex_table(volume, efficiency, remediation, paper)
    tex_path = os.path.join(args.output_dir, "table_communication.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex)
    print(f"Saved LaTeX: {tex_path}")


if __name__ == "__main__":
    main()
