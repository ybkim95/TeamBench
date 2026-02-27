"""
TeamBench ablation study framework.

Tests whether each architectural component (information partition,
permission partition, verification independence) contributes to
benchmark results.

Ablation conditions:
  A. Oracle: Single agent, full access (spec + workspace + exec)
     -> Upper bound on solvability
  B. Restricted: Single agent, executor-only access (brief + workspace + exec)
     -> Lower bound / single-agent baseline
  C. Team-NoVerify: Planner + Executor (no Verifier, no remediation)
     -> Tests verification value
  D. Team-NoPlan: Executor + Verifier (no Planner, executor gets brief only)
     -> Tests planning value
  E. Full: Planner + Executor + Verifier with remediation
     -> Full team baseline

Metrics computed:
  - TNI = (S_team - S_restricted) / max(eps, S_oracle - S_restricted)
  - Planning Value = S_full - S_team_no_plan
  - Verification Value = S_full - S_team_no_verify
  - Remediation Value = S_full_with_remediation - S_full_no_remediation
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from harness.agent_interface import (
    RoleConfig,
    RunCommandTool,
    ReadFileTool,
    WriteFileTool,
    SendMessageTool,
    ToolCallAdapter,
    make_planner_config,
    make_executor_config,
    make_verifier_config,
)
from harness.agent_loop import AgentLoop
from harness.orchestrator import TaskOrchestrator, OrchestratorResult, PhaseResult, _relay_planner_text
from harness.run_all import discover_tasks, setup_run, grade_run


class AblationCondition(str, Enum):
    ORACLE = "oracle"
    RESTRICTED = "restricted"
    TEAM_NO_VERIFY = "team_no_verify"
    TEAM_NO_PLAN = "team_no_plan"
    FULL = "full"
    # New expertise-asymmetry conditions
    EXPERTISE_FULL = "expertise_full"
    EXPERTISE_NO_ANALYSIS = "expertise_no_analysis"
    EXPERTISE_NO_TEST = "expertise_no_test"
    EXPERTISE_ORACLE = "expertise_oracle"


@dataclass
class AblationRun:
    condition: AblationCondition
    task_id: str
    seed: int
    run_id: str = ""
    run_dir: str = ""
    score: dict = field(default_factory=dict)
    elapsed_sec: float = 0.0
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        return bool(self.score.get("pass", False))


def _make_oracle_config(
    spec_path: str,
    workspace_dir: str,
    reports_dir: str,
    messages_dir: str,
    submission_dir: str,
    task_dir: str,
) -> RoleConfig:
    """Oracle: single agent with full access (spec + workspace + exec + write + attestation)."""
    from harness.agent_interface import _build_path_map
    pm = _build_path_map(
        workspace_dir=workspace_dir,
        reports_dir=reports_dir,
        messages_dir=messages_dir,
        submission_dir=submission_dir,
        task_dir=task_dir,
    )
    return RoleConfig(
        role="oracle",
        system_prompt=(
            "You are an Oracle agent with FULL access to the task specification and workspace.\n"
            "You can execute commands, read/write any allowed file, and write the attestation.\n"
            "Your goal: complete the task and write attestation.json with verdict='pass'.\n\n"
            "IMPORTANT workflow:\n"
            "1. Read the spec (already provided) to understand ALL requirements.\n"
            "2. Read relevant workspace files ONCE to understand current state.\n"
            "3. TAKE ACTION: modify files using write() or run commands to fix issues.\n"
            "4. Verify your changes work by running tests or checking output.\n"
            "5. Write attestation.json and output DONE.\n\n"
            "DO NOT read the same file more than twice. After reading, ACT on what you learned.\n"
            "If you are unsure, make your best attempt rather than re-reading files.\n"
            "Use run(cmd=...) for commands, read(path=...) for files, write(path=..., content=...) for edits.\n"
            "Output DONE when complete."
        ),
        tools=[
            RunCommandTool(cwd=workspace_dir, allowed=True),
            ReadFileTool(
                allowed_roots=[task_dir, workspace_dir, reports_dir, messages_dir, submission_dir],
                path_map=pm,
                base_dir=workspace_dir,
            ),
            WriteFileTool(
                allowed_roots=[workspace_dir, reports_dir, submission_dir],
                path_map=pm,
                base_dir=workspace_dir,
            ),
            SendMessageTool(messages_dir=messages_dir, sender_role="oracle"),
        ],
    )


def _make_restricted_config(
    brief_path: str,
    workspace_dir: str,
    reports_dir: str,
    messages_dir: str,
    submission_dir: str,
    task_dir: str,
) -> RoleConfig:
    """Restricted: single agent with executor-only access (brief + workspace + exec + write)."""
    from harness.agent_interface import _build_path_map
    pm = _build_path_map(
        workspace_dir=workspace_dir,
        reports_dir=reports_dir,
        messages_dir=messages_dir,
        submission_dir=submission_dir,
        task_dir=task_dir,
    )
    return RoleConfig(
        role="restricted",
        system_prompt=(
            "You are a Restricted agent. You can only see the brief summary (not the full spec).\n"
            "You can execute commands and read/write files in the workspace.\n"
            "Your goal: complete the task as described in the brief and write attestation.json.\n"
            "Use run(cmd=...) to execute commands in the workspace.\n"
            "Use read(path=...) and write(path=...) for files.\n"
            "Write attestation.json in the submission directory when done.\n"
            "Output DONE when complete."
        ),
        tools=[
            RunCommandTool(cwd=workspace_dir, allowed=True),
            ReadFileTool(
                allowed_roots=[os.path.dirname(brief_path), workspace_dir, reports_dir, messages_dir],
                path_map=pm,
                base_dir=workspace_dir,
            ),
            WriteFileTool(
                allowed_roots=[workspace_dir, reports_dir, submission_dir],
                path_map=pm,
                base_dir=workspace_dir,
            ),
            SendMessageTool(messages_dir=messages_dir, sender_role="restricted"),
        ],
    )


def _write_passing_attestation(submission_dir: str, task_id: str) -> None:
    """Write a stub passing attestation (used for TEAM_NO_VERIFY condition)."""
    os.makedirs(submission_dir, exist_ok=True)
    att = {"task_id": task_id, "verdict": "pass", "checklist": [], "condition": "team_no_verify_stub"}
    att_path = os.path.join(submission_dir, "attestation.json")
    with open(att_path, "w", encoding="utf-8") as f:
        json.dump(att, f, indent=2)


def run_ablation_condition(
    condition: AblationCondition,
    task_dir: str,
    run_dir: str,
    adapter: ToolCallAdapter,
    max_turns: int = 20,
    max_remediation: int = 2,
) -> OrchestratorResult:
    """
    Configure and run the orchestrator differently per ablation condition.

    Returns an OrchestratorResult with verdict set based on attestation.
    """
    task_id = os.path.basename(task_dir)
    spec_path = os.path.join(task_dir, "spec.md")
    brief_path = os.path.join(task_dir, "brief.md")

    workspace = os.path.join(run_dir, "workspace")
    reports = os.path.join(run_dir, "reports")
    messages = os.path.join(run_dir, "messages")
    submission = os.path.join(run_dir, "submission")
    logs = os.path.join(run_dir, "logs")

    def read_file(path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    spec_text = read_file(spec_path)
    brief_text = read_file(brief_path)
    result = OrchestratorResult(task_id=task_id)

    if condition == AblationCondition.ORACLE:
        # Single agent with full access to spec + workspace + exec
        oracle_config = _make_oracle_config(
            spec_path=spec_path,
            workspace_dir=workspace,
            reports_dir=reports,
            messages_dir=messages,
            submission_dir=submission,
            task_dir=task_dir,
        )
        loop = AgentLoop(
            role_config=oracle_config,
            adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "oracle"),
            max_turns=max_turns,
        )
        prompt = (
            f"You are the Oracle for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"## Instructions\n"
            f"Complete the task requirements. Then write attestation.json with:\n"
            f'  write(path="attestation.json", content=\'{{"task_id":"{task_id}","verdict":"pass","checklist":[]}}\')\n'
            f"Output DONE when complete."
        )
        turns = loop.run(prompt)
        phase = PhaseResult(phase="oracle", turns=turns)
        result.phases.append(phase)
        result.total_turns += len(turns)

    elif condition == AblationCondition.RESTRICTED:
        # Single agent with executor-only access (brief only)
        restricted_config = _make_restricted_config(
            brief_path=brief_path,
            workspace_dir=workspace,
            reports_dir=reports,
            messages_dir=messages,
            submission_dir=submission,
            task_dir=task_dir,
        )
        loop = AgentLoop(
            role_config=restricted_config,
            adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "restricted"),
            max_turns=max_turns,
        )
        prompt = (
            f"You are a Restricted agent for task: {task_id}\n\n"
            f"## Brief\n{brief_text}\n\n"
            f"## Instructions\n"
            f"Complete the task. Then write attestation.json with:\n"
            f'  write(path="attestation.json", content=\'{{"task_id":"{task_id}","verdict":"pass","checklist":[]}}\')\n'
            f"Output DONE when complete."
        )
        turns = loop.run(prompt)
        phase = PhaseResult(phase="restricted", turns=turns)
        result.phases.append(phase)
        result.total_turns += len(turns)

    elif condition == AblationCondition.TEAM_NO_VERIFY:
        # Planner + Executor phases only — no Verifier, auto-write passing attestation
        planner_config = make_planner_config(
            spec_path=spec_path, messages_dir=messages, task_dir=task_dir,
        )
        planner_loop = AgentLoop(
            role_config=planner_config, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "planner"),
            max_turns=max_turns,
        )
        planner_prompt = (
            f"You are the Planner for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"## Instructions\n"
            f"Create a plan and send it to the Executor via send_message(to='executor', content=...).\n"
            f"Output DONE when done."
        )
        planner_turns = planner_loop.run(planner_prompt)
        phase1 = PhaseResult(phase="planning", turns=planner_turns)
        result.phases.append(phase1)
        result.total_turns += len(planner_turns)
        _relay_planner_text(planner_turns, messages)

        executor_config = make_executor_config(
            brief_path=brief_path, workspace_dir=workspace, reports_dir=reports,
            messages_dir=messages, submission_dir=submission, task_dir=task_dir,
        )
        executor_loop = AgentLoop(
            role_config=executor_config, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "executor"),
            max_turns=max_turns,
        )
        executor_prompt = (
            f"You are the Executor for task: {task_id}\n\n"
            f"## Brief\n{brief_text}\n\n"
            f"## Instructions\n"
            f"Check messages from the Planner, then complete the task.\n"
            f"Output DONE when done."
        )
        executor_turns = executor_loop.run(executor_prompt)
        phase2 = PhaseResult(phase="execution", turns=executor_turns)
        result.phases.append(phase2)
        result.total_turns += len(executor_turns)

        # Auto-write passing attestation (no verifier)
        _write_passing_attestation(submission, task_id)

    elif condition == AblationCondition.TEAM_NO_PLAN:
        # Skip planning — Executor gets brief only, then Verifier checks
        executor_config = make_executor_config(
            brief_path=brief_path, workspace_dir=workspace, reports_dir=reports,
            messages_dir=messages, submission_dir=submission, task_dir=task_dir,
        )
        executor_loop = AgentLoop(
            role_config=executor_config, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "executor"),
            max_turns=max_turns,
        )
        executor_prompt = (
            f"You are the Executor for task: {task_id}\n\n"
            f"## Brief\n{brief_text}\n\n"
            f"## Instructions\n"
            f"Complete the task based on the brief. No Planner is available.\n"
            f"Send a completion message to the Verifier when done.\n"
            f"Output DONE when done."
        )
        executor_turns = executor_loop.run(executor_prompt)
        phase1 = PhaseResult(phase="execution", turns=executor_turns)
        result.phases.append(phase1)
        result.total_turns += len(executor_turns)

        verifier_config = make_verifier_config(
            spec_path=spec_path, workspace_dir=workspace, reports_dir=reports,
            messages_dir=messages, submission_dir=submission, task_dir=task_dir,
        )
        verifier_loop = AgentLoop(
            role_config=verifier_config, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "verifier", "attempt_0"),
            max_turns=max_turns,
        )
        verifier_prompt = (
            f"You are the Verifier for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"## Instructions\n"
            f"Verify the workspace against the spec. Write attestation.json.\n"
            f"Output DONE when done."
        )
        verifier_turns = verifier_loop.run(verifier_prompt)
        phase2 = PhaseResult(phase="verification_0", turns=verifier_turns)
        result.phases.append(phase2)
        result.total_turns += len(verifier_turns)

    elif condition == AblationCondition.FULL:
        # Normal 3-phase orchestrator with remediation
        orchestrator = TaskOrchestrator(
            task_dir=task_dir,
            run_dir=run_dir,
            adapter=adapter,
            max_turns_per_phase=max_turns,
            max_remediation_loops=max_remediation,
        )
        return orchestrator.run()

    elif condition == AblationCondition.EXPERTISE_FULL:
        # Full expertise team: analysis planner + executor + test verifier
        from harness.orchestrator import ExpertiseOrchestrator
        orch = ExpertiseOrchestrator(
            task_dir=task_dir,
            run_dir=run_dir,
            adapter=adapter,
            max_planner_turns=15,
            max_executor_turns=max_turns,
            max_verifier_turns=15,
            max_remediation_loops=max_remediation,
        )
        return orch.run()

    elif condition == AblationCondition.EXPERTISE_NO_ANALYSIS:
        # Executor (receives no analysis) + expertise verifier (runs tests)
        # Measures value of Planner analysis
        executor_config = make_executor_config(
            brief_path=brief_path, workspace_dir=workspace, reports_dir=reports,
            messages_dir=messages, submission_dir=submission, task_dir=task_dir,
        )
        executor_loop = AgentLoop(
            role_config=executor_config, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "executor"),
            max_turns=max_turns,
        )
        executor_prompt = (
            f"You are the Executor for task: {task_id}\n\n"
            f"## Brief\n{brief_text}\n\n"
            f"Complete the task based on the brief. No Planner analysis is available.\n"
            f"Output DONE when done."
        )
        executor_turns = executor_loop.run(executor_prompt)
        phase1 = PhaseResult(phase="execution", turns=executor_turns)
        result.phases.append(phase1)
        result.total_turns += len(executor_turns)

        from harness.agent_interface import make_expertise_verifier_config
        verifier_config = make_expertise_verifier_config(
            spec_path=spec_path, workspace_dir=workspace, reports_dir=reports,
            messages_dir=messages, submission_dir=submission, task_dir=task_dir,
        )
        verifier_loop = AgentLoop(
            role_config=verifier_config, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "verifier", "attempt_0"),
            max_turns=15,
        )
        verifier_prompt = (
            f"You are the Verifier for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"Run tests to verify the workspace. Write attestation.json.\n"
            f"Output DONE when done."
        )
        verifier_turns = verifier_loop.run(verifier_prompt)
        phase2 = PhaseResult(phase="verification_0", turns=verifier_turns)
        result.phases.append(phase2)
        result.total_turns += len(verifier_turns)

    elif condition == AblationCondition.EXPERTISE_NO_TEST:
        # Analysis planner + executor, but verifier only reads (no test execution)
        # Measures value of Verifier test execution
        from harness.agent_interface import make_analysis_planner_config
        analysis_dir = os.path.join(run_dir, "analysis")
        os.makedirs(analysis_dir, exist_ok=True)

        planner_config = make_analysis_planner_config(
            spec_path=spec_path, messages_dir=messages,
            workspace_dir=workspace, analysis_dir=analysis_dir, task_dir=task_dir,
        )
        planner_loop = AgentLoop(
            role_config=planner_config, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "planner"),
            max_turns=15,
        )
        planner_prompt = (
            f"You are the Planner for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"Run static analysis, write /analysis/planner_report.md, send summary to executor.\n"
            f"Output DONE when done."
        )
        planner_turns = planner_loop.run(planner_prompt)
        phase1 = PhaseResult(phase="planner_analysis", turns=planner_turns)
        result.phases.append(phase1)
        result.total_turns += len(planner_turns)
        _relay_planner_text(planner_turns, messages)

        executor_config = make_executor_config(
            brief_path=brief_path, workspace_dir=workspace, reports_dir=reports,
            messages_dir=messages, submission_dir=submission, task_dir=task_dir,
        )
        executor_loop = AgentLoop(
            role_config=executor_config, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "executor"),
            max_turns=max_turns,
        )
        executor_prompt = (
            f"You are the Executor for task: {task_id}\n\n"
            f"## Brief\n{brief_text}\n\n"
            f"Read the Planner's analysis at /analysis/planner_report.md, then implement fixes.\n"
            f"Output DONE when done."
        )
        executor_turns = executor_loop.run(executor_prompt)
        phase2 = PhaseResult(phase="execution", turns=executor_turns)
        result.phases.append(phase2)
        result.total_turns += len(executor_turns)

        # Static verifier (read-only, no test execution)
        verifier_config = make_verifier_config(
            spec_path=spec_path, workspace_dir=workspace, reports_dir=reports,
            messages_dir=messages, submission_dir=submission, task_dir=task_dir,
        )
        verifier_loop = AgentLoop(
            role_config=verifier_config, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "verifier", "attempt_0"),
            max_turns=15,
        )
        verifier_prompt = (
            f"You are the Verifier for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"Read workspace files to verify requirements. Write attestation.json.\n"
            f"Output DONE when done."
        )
        verifier_turns = verifier_loop.run(verifier_prompt)
        phase3 = PhaseResult(phase="verification_0", turns=verifier_turns)
        result.phases.append(phase3)
        result.total_turns += len(verifier_turns)

    elif condition == AblationCondition.EXPERTISE_ORACLE:
        # Single agent with all tools + full spec (expertise upper bound)
        oracle_config = _make_oracle_config(
            spec_path=spec_path, workspace_dir=workspace, reports_dir=reports,
            messages_dir=messages, submission_dir=submission, task_dir=task_dir,
        )
        loop = AgentLoop(
            role_config=oracle_config, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "expertise_oracle"),
            max_turns=max_turns,
        )
        prompt = (
            f"You are the Oracle for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"Complete all requirements. Write attestation.json when done.\n"
            f"Output DONE when complete."
        )
        turns = loop.run(prompt)
        phase = PhaseResult(phase="expertise_oracle", turns=turns)
        result.phases.append(phase)
        result.total_turns += len(turns)

    # Check attestation verdict for non-FULL conditions
    att_path = os.path.join(submission, "attestation.json")
    try:
        with open(att_path, "r", encoding="utf-8") as f:
            att = json.load(f)
        result.verdict = att.get("verdict", "fail")
    except (FileNotFoundError, json.JSONDecodeError):
        result.verdict = "fail"

    return result


def compute_ablation_metrics(
    condition_scores: dict[AblationCondition, list[bool]],
    epsilon: float = 0.01,
    condition_partial: dict[AblationCondition, list[float]] | None = None,
) -> dict:
    """
    Compute ablation metrics from per-condition scores.

    Uses partial scores (0.0-1.0) when available for more granular TNI,
    falls back to binary pass/fail rates.

    Args:
        condition_scores: mapping from AblationCondition to list of bool (True=pass)
        epsilon: minimum denominator for TNI to avoid division by zero
        condition_partial: optional mapping from AblationCondition to list of float (0.0-1.0)

    Returns:
        dict with TNI, planning_value, verification_value, and per-condition rates
    """
    def rate(scores: list[bool]) -> float:
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def avg_partial(scores: list[float]) -> float:
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    s_oracle = rate(condition_scores.get(AblationCondition.ORACLE, []))
    s_restricted = rate(condition_scores.get(AblationCondition.RESTRICTED, []))
    s_full = rate(condition_scores.get(AblationCondition.FULL, []))
    s_no_verify = rate(condition_scores.get(AblationCondition.TEAM_NO_VERIFY, []))
    s_no_plan = rate(condition_scores.get(AblationCondition.TEAM_NO_PLAN, []))

    # Partial-score TNI (more granular than binary)
    if condition_partial:
        p_oracle = avg_partial(condition_partial.get(AblationCondition.ORACLE, []))
        p_restricted = avg_partial(condition_partial.get(AblationCondition.RESTRICTED, []))
        p_full = avg_partial(condition_partial.get(AblationCondition.FULL, []))
        p_no_verify = avg_partial(condition_partial.get(AblationCondition.TEAM_NO_VERIFY, []))
        p_no_plan = avg_partial(condition_partial.get(AblationCondition.TEAM_NO_PLAN, []))
    else:
        p_oracle, p_restricted, p_full = s_oracle, s_restricted, s_full
        p_no_verify, p_no_plan = s_no_verify, s_no_plan

    necessity_gap = p_oracle - p_restricted
    tni = (p_full - p_restricted) / max(epsilon, necessity_gap)
    team_uplift = p_full - p_restricted  # Always valid, no oracle dependency
    collab_efficiency = (p_full - p_restricted) / max(epsilon, p_oracle) if p_oracle > epsilon else 0.0
    planning_value = p_full - p_no_plan
    verification_value = p_full - p_no_verify

    # Expertise-asymmetry metrics
    s_expertise_full = rate(condition_scores.get(AblationCondition.EXPERTISE_FULL, []))
    s_expertise_no_analysis = rate(condition_scores.get(AblationCondition.EXPERTISE_NO_ANALYSIS, []))
    s_expertise_no_test = rate(condition_scores.get(AblationCondition.EXPERTISE_NO_TEST, []))
    s_expertise_oracle = rate(condition_scores.get(AblationCondition.EXPERTISE_ORACLE, []))

    if condition_partial:
        p_expertise_full = avg_partial(condition_partial.get(AblationCondition.EXPERTISE_FULL, []))
        p_expertise_no_analysis = avg_partial(condition_partial.get(AblationCondition.EXPERTISE_NO_ANALYSIS, []))
        p_expertise_no_test = avg_partial(condition_partial.get(AblationCondition.EXPERTISE_NO_TEST, []))
        p_expertise_oracle = avg_partial(condition_partial.get(AblationCondition.EXPERTISE_ORACLE, []))
    else:
        p_expertise_full = s_expertise_full
        p_expertise_no_analysis = s_expertise_no_analysis
        p_expertise_no_test = s_expertise_no_test
        p_expertise_oracle = s_expertise_oracle

    analysis_value = p_expertise_full - p_expertise_no_analysis
    testing_value = p_expertise_full - p_expertise_no_test
    expertise_necessity_gap = p_expertise_oracle - p_restricted
    expertise_tni = (p_expertise_full - p_restricted) / max(epsilon, expertise_necessity_gap)

    return {
        "s_oracle": round(s_oracle, 4),
        "s_restricted": round(s_restricted, 4),
        "s_full": round(s_full, 4),
        "s_no_verify": round(s_no_verify, 4),
        "s_no_plan": round(s_no_plan, 4),
        "p_oracle": round(p_oracle, 4),
        "p_restricted": round(p_restricted, 4),
        "p_full": round(p_full, 4),
        "p_no_verify": round(p_no_verify, 4),
        "p_no_plan": round(p_no_plan, 4),
        "necessity_gap": round(necessity_gap, 4),
        "tni": round(tni, 4),
        "team_uplift": round(team_uplift, 4),
        "collab_efficiency": round(collab_efficiency, 4),
        "planning_value": round(planning_value, 4),
        "verification_value": round(verification_value, 4),
        "s_expertise_full": round(s_expertise_full, 4),
        "s_expertise_no_analysis": round(s_expertise_no_analysis, 4),
        "s_expertise_no_test": round(s_expertise_no_test, 4),
        "s_expertise_oracle": round(s_expertise_oracle, 4),
        "p_expertise_full": round(p_expertise_full, 4),
        "p_expertise_no_analysis": round(p_expertise_no_analysis, 4),
        "p_expertise_no_test": round(p_expertise_no_test, 4),
        "p_expertise_oracle": round(p_expertise_oracle, 4),
        "analysis_value": round(analysis_value, 4),
        "testing_value": round(testing_value, 4),
        "expertise_tni": round(expertise_tni, 4),
        "interpretation": {
            "tni": _interpret_tni(tni),
            "team_uplift": f"Team adds {team_uplift:+.1%} over single agent",
            "collab_efficiency": f"Team reaches {collab_efficiency:.1%} of oracle ceiling via collaboration",
            "planning_value": f"Planning adds {planning_value:+.1%} partial score",
            "verification_value": f"Verification adds {verification_value:+.1%} partial score",
        },
    }


def _interpret_tni(tni: float) -> str:
    if tni >= 0.9:
        return "Teamwork fully recovers the performance gap."
    elif tni >= 0.5:
        return "Teamwork substantially recovers the performance gap."
    elif tni >= 0.1:
        return "Teamwork provides modest improvement."
    elif tni >= 0.0:
        return "Teamwork provides minimal improvement."
    else:
        return "Teamwork is harmful (negative collaboration gain)."


def run_full_ablation(
    model: str,
    tasks: Optional[list[str]],
    seeds: list[int],
    tasks_dir: str,
    output: str,
    max_turns: int = 20,
    max_remediation: int = 2,
    conditions: Optional[list[AblationCondition]] = None,
) -> dict:
    """
    Run ablation conditions for given tasks and seeds.

    Args:
        model: model name (determines adapter)
        tasks: task names to run (None = all)
        seeds: seeds to run
        tasks_dir: base tasks directory
        output: path to write ablation_results.json
        max_turns: max turns per agent phase
        max_remediation: max remediation loops (used for FULL condition)
        conditions: which conditions to run (None = all)

    Returns:
        Full ablation results dict.
    """
    from harness.adapters import create_adapter

    tasks_dir = os.path.abspath(tasks_dir)
    task_names = tasks or discover_tasks(tasks_dir)

    adapter = create_adapter(model=model, temperature=0.2)

    conditions = conditions if conditions is not None else list(AblationCondition)

    print(f"TeamBench Ablation Study")
    print(f"Model: {model}")
    print(f"Tasks: {task_names}")
    print(f"Seeds: {seeds}")
    print(f"Conditions: {[c.value for c in conditions]}")
    print("=" * 60)

    all_runs: list[dict] = []
    # condition -> list of bool (pass/fail)
    condition_scores: dict[AblationCondition, list[bool]] = {c: [] for c in conditions}
    # condition -> list of float (partial scores 0.0-1.0)
    condition_partial: dict[AblationCondition, list[float]] = {c: [] for c in conditions}

    runs_base = os.path.join(os.path.dirname(output), "ablation_runs")

    total = len(conditions) * len(task_names) * len(seeds)
    i = 0

    for condition in conditions:
        for task_name in task_names:
            for seed in seeds:
                i += 1
                print(f"\n[{i}/{total}] {condition.value} x {task_name} (seed={seed})")
                start_time = time.time()

                run_record = AblationRun(
                    condition=condition,
                    task_id=task_name,
                    seed=seed,
                )

                try:
                    run_id, run_dir, task_dir = setup_run(
                        task_name, tasks_dir, runs_base, seed=seed
                    )
                    run_record.run_id = run_id
                    run_record.run_dir = run_dir

                    # Store condition in run_meta.json for post-hoc analysis
                    meta_path = os.path.join(run_dir, "run_meta.json")
                    if os.path.isfile(meta_path):
                        with open(meta_path, "r") as mf:
                            meta = json.load(mf)
                        meta["condition"] = condition.value
                        with open(meta_path, "w") as mf:
                            json.dump(meta, mf, indent=2)

                    orch_result = run_ablation_condition(
                        condition=condition,
                        task_dir=task_dir,
                        run_dir=run_dir,
                        adapter=adapter,
                        max_turns=max_turns,
                        max_remediation=max_remediation,
                    )

                    elapsed = time.time() - start_time
                    score = grade_run(task_name, task_dir, run_dir)
                    run_record.score = score
                    run_record.elapsed_sec = round(elapsed, 1)

                    condition_scores[condition].append(bool(score.get("pass", False)))
                    partial = score.get("secondary", {}).get("partial_score", 1.0 if score.get("pass") else 0.0)
                    condition_partial[condition].append(float(partial))
                    status = "PASS" if score.get("pass") else "FAIL"
                    print(f"  {status} (partial={partial:.2f}, {elapsed:.1f}s, {orch_result.total_turns} turns)")

                except Exception as e:
                    run_record.error = str(e)
                    run_record.elapsed_sec = round(time.time() - start_time, 1)
                    condition_scores[condition].append(False)
                    condition_partial[condition].append(0.0)
                    print(f"  ERROR: {e}")

                partial_score = run_record.score.get("secondary", {}).get(
                    "partial_score", 1.0 if run_record.passed else 0.0
                )
                all_runs.append({
                    "condition": condition.value,
                    "task_id": task_name,
                    "seed": seed,
                    "run_id": run_record.run_id,
                    "run_dir": run_record.run_dir,
                    "pass": run_record.passed,
                    "partial_score": partial_score,
                    "elapsed_sec": run_record.elapsed_sec,
                    "failure_modes": run_record.score.get("failure_modes", []),
                    "error": run_record.error,
                })

    metrics = compute_ablation_metrics(condition_scores, condition_partial=condition_partial)

    report = {
        "model": model,
        "tasks": task_names,
        "seeds": seeds,
        "completed": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "per_condition": {
            c.value: {
                "passes": sum(condition_scores[c]),
                "total": len(condition_scores[c]),
                "success_rate": round(
                    sum(condition_scores[c]) / max(1, len(condition_scores[c])), 4
                ),
            }
            for c in conditions
        },
        "runs": all_runs,
    }

    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"ABLATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Condition           Passes  Total  Rate")
    for c in conditions:
        passes = sum(condition_scores[c])
        total_c = len(condition_scores[c])
        rate = passes / max(1, total_c)
        print(f"  {c.value:20s}  {passes:5d}  {total_c:5d}  {rate:.1%}")
    print(f"\n  Metrics:")
    print(f"  TNI:                {metrics['tni']:.4f}  ({metrics['interpretation']['tni']})")
    print(f"  Planning Value:     {metrics['planning_value']:+.4f}")
    print(f"  Verification Value: {metrics['verification_value']:+.4f}")
    print(f"\n  Report: {output}")

    return report


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="TeamBench ablation study")
    ap.add_argument("--model", required=True, help="Model name")
    ap.add_argument("--tasks", nargs="*", default=None, help="Tasks (default: all)")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2], help="Seeds")
    ap.add_argument("--tasks-dir", default="tasks", help="Tasks directory")
    ap.add_argument("--output", default="shared/ablation_results.json", help="Output path")
    ap.add_argument("--max-turns", type=int, default=20, help="Max turns per phase")
    ap.add_argument("--max-remediation", type=int, default=2, help="Max remediation loops")
    ap.add_argument(
        "--conditions",
        nargs="+",
        default=None,
        choices=[c.value for c in AblationCondition],
        help="Conditions to run (default: all). E.g. --conditions expertise_full expertise_oracle",
    )
    args = ap.parse_args()

    conditions = (
        [AblationCondition(c) for c in args.conditions] if args.conditions else None
    )

    # Load .env if present
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.isfile(env_path):
        with open(env_path) as ef:
            for line in ef:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())

    run_full_ablation(
        model=args.model,
        tasks=args.tasks,
        seeds=args.seeds,
        tasks_dir=os.path.abspath(args.tasks_dir),
        output=args.output,
        max_turns=args.max_turns,
        max_remediation=args.max_remediation,
        conditions=conditions,
    )


if __name__ == "__main__":
    main()
