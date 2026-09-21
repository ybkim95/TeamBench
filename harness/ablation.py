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

import hashlib
import json
import os
import tempfile
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
from harness.agent_loop import AgentLoop, TurnBudget
from harness.orchestrator import TaskOrchestrator, OrchestratorResult, PhaseResult, _relay_planner_text
from harness.run_all import discover_tasks, setup_run, grade_run


class AblationCondition(str, Enum):
    ORACLE = "oracle"
    RESTRICTED = "restricted"
    TEAM_NO_VERIFY = "team_no_verify"
    TEAM_NO_PLAN = "team_no_plan"
    FULL = "full"
    # Heterogeneous team: different models per role
    HETERO = "hetero"
    # New expertise-asymmetry conditions
    EXPERTISE_FULL = "expertise_full"
    EXPERTISE_NO_ANALYSIS = "expertise_no_analysis"
    EXPERTISE_NO_TEST = "expertise_no_test"
    EXPERTISE_ORACLE = "expertise_oracle"
    # Strong baselines — single agent with enhanced prompting
    ORACLE_COT = "oracle_cot"
    ORACLE_2PASS = "oracle_2pass"
    # Budget-matched Solo: same total turn budget as the Full team (15+25+10=50)
    ORACLE_BUDGET_MATCHED = "oracle_budget_matched"
    # Topology ablation — different coordination patterns
    TOPO_ITERATIVE = "topo_iterative"        # Planner <-> Executor multi-round
    TOPO_DUAL_EXEC = "topo_dual_exec"        # Planner -> 2x Executor -> Verifier selects
    TOPO_VERIFY_FIRST = "topo_verify_first"  # Verifier(gap analysis) -> Executor -> Verifier(check)
    TOPO_SELF_CHECK = "topo_self_check"      # Single agent with structured implement->verify->fix
    # role_enforcement_ablation experiment (experiments/role_enforcement_ablation/)
    # ENFORCED is a semantic alias for FULL; kept as a separate enum value so the
    # experiment records read cleanly ("condition: enforced") in analysis output.
    PROMPT_ONLY = "prompt_only"                          # shared workspace + shared history
    ENFORCED_SHARED_HISTORY = "enforced_shared_history"  # OS isolation on workspace, shared history
    ENFORCED = "enforced"                                # alias for FULL (OS isolation both axes)


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


def _usage_snapshot(adapter) -> dict:
    """Cumulative token counters off an adapter, or zeros if it keeps none.

    Every adapter already accumulates usage, but nothing ever persisted it, so
    a finished campaign could report turns and wall-clock and not tokens. That
    left the compute-matching claim answerable only in turns: a reviewer asking
    "matched turns, but was the token spend matched?" had no data to read.
    """
    try:
        u = adapter.get_usage() or {}
    except Exception:
        return {"input_tokens": 0, "output_tokens": 0}
    return {"input_tokens": int(u.get("input_tokens") or 0),
            "output_tokens": int(u.get("output_tokens") or 0)}


def _usage_delta(adapter, before: dict) -> dict:
    """Tokens attributable to one run.

    The adapter is built once per campaign and its counters are cumulative, so
    a per-run figure is the difference against the snapshot taken before the
    run. Recorded for failed and errored runs too: a run that spent zero tokens
    is direct evidence it never reached the model.
    """
    after = _usage_snapshot(adapter)
    d = {k: max(0, after.get(k, 0) - before.get(k, 0)) for k in
         ("input_tokens", "output_tokens")}
    d["total_tokens"] = d["input_tokens"] + d["output_tokens"]
    return d


def _fallback_path(primary: str) -> str:
    """Local sidecar for a checkpoint whose real home is unwritable.

    Deliberately on local disk: the whole point is to survive the network
    filesystem being unavailable.
    """
    h = hashlib.sha1(os.path.abspath(primary).encode()).hexdigest()[:12]
    d = os.path.join(tempfile.gettempdir(), "teambench_checkpoint_fallback")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "%s__%s" % (h, os.path.basename(primary)))


def durable_append(primary: str, line: str) -> None:
    """Append one checkpoint line, and do not lose it to a filesystem error.

    The repository lives on an NFS mount with sec=krb5p, so every write needs a
    live Kerberos ticket. Tickets here last two days and cannot be renewed once
    they lapse, and the kernel caches a GSS context for a while after that, so
    a job runs normally and then dies mid-flight. That is what ended a 288-run
    sweep after 6 runs: OSError Errno 127, "Key has expired", raised out of this
    very append and taking the whole campaign with it.

    A completed run is expensive and already paid for. Losing it because a
    ticket lapsed is the wrong failure. So: retry briefly, then write to local
    disk and keep going. The run is never lost and the campaign never dies here.
    """
    err = None
    for attempt in range(3):
        try:
            with open(primary, "a") as f:
                f.write(line)
            return
        except OSError as e:
            err = e
            time.sleep(1.5 * (attempt + 1))
    fb = _fallback_path(primary)
    try:
        with open(fb, "a") as f:
            f.write(line)
        print("  [checkpoint] %s unwritable (%s); appended to %s instead. "
              "Merge with: cat %s >> %s"
              % (primary, err, fb, fb, primary), flush=True)
    except OSError as e2:
        # Both destinations gone. Say so loudly; do not pretend it was written.
        print("  [checkpoint] LOST a completed run: primary %s (%s) and "
              "fallback %s (%s) both unwritable" % (primary, err, fb, e2),
              flush=True)


class CredentialFailure(RuntimeError):
    """The provider rejected our credential, so no further run can measure anything."""


def _is_credential_failure(exc: BaseException) -> bool:
    """True for an authentication rejection, which is terminal for a sweep.

    Deliberately narrow. A 429 or a 5xx is transient and the adapter already
    retries those; only a rejected key is treated as fatal, because it cannot
    recover without a human and every subsequent run would be recorded as a
    zero that looks like a real failure.
    """
    t = str(exc)
    return ("authentication_error" in t
            or "Error code: 401" in t
            or "invalid x-api-key" in t
            or "API key is invalid" in t)


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
            "When done, write attestation.json to the submission directory using:\n"
            '  write(path="../submission/attestation.json", content=\'...\')\n'
            "Then output DONE."
        ),
        tools=[
            RunCommandTool(cwd=workspace_dir, allowed=True),
            ReadFileTool(
                allowed_roots=[
                    os.path.dirname(brief_path), workspace_dir,
                    reports_dir, messages_dir, submission_dir,
                ],
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
    model_config: Optional[dict] = None,
    total_turns: int = 60,
) -> OrchestratorResult:
    """
    Configure and run the orchestrator differently per ablation condition.

    Returns an OrchestratorResult with verdict set based on attestation.

    Compute matching: `total_turns` is the LLM-turn allowance for the ENTIRE run and
    is identical across conditions. It is enforced by a single TurnBudget shared by
    every phase, so a three-role team with two remediation rounds and a single Solo
    agent spend from the same pool. `max_turns` remains the per-phase ceiling, which
    stops one role from consuming the whole run, but it is no longer what determines
    a condition's total compute. Before this change Solo ran at 20 turns against a
    Full Team at up to 140, and every Solo-versus-Team contrast in the paper was
    confounded with that gap.
    """
    task_id = os.path.basename(task_dir)
    budget = TurnBudget(total_turns)
    # Per-phase caps are derived from the shared budget so that a condition's
    # nominal phases divide it evenly. The budget is what actually binds; these
    # caps only stop one role from starving the roles that follow it.
    phase_turns_2 = total_turns // 2   # two-role teams
    phase_turns_3 = total_turns // 3   # three-role team
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

    if condition == AblationCondition.ORACLE or condition == AblationCondition.ORACLE_BUDGET_MATCHED:
        # Single agent with full access to spec + workspace + exec.
        # ORACLE_BUDGET_MATCHED gives the Solo agent the team's full turn budget
        # (Planner 15 + Executor 25 + Verifier 10 = 50) so a reviewer cannot
        # attribute the team gain to compute alone.
        oracle_config = _make_oracle_config(
            spec_path=spec_path,
            workspace_dir=workspace,
            reports_dir=reports,
            messages_dir=messages,
            submission_dir=submission,
            task_dir=task_dir,
        )
        # A single-role condition has one phase, so its per-phase cap must equal the
        # run budget or it stops early and the comparison is not compute-matched.
        # ORACLE_BUDGET_MATCHED previously hardcoded 50 against a real team ceiling
        # of 140; it is now redundant with the shared budget and kept only as a label.
        run_max_turns = total_turns
        loop = AgentLoop(
            role_config=oracle_config,
            adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, condition.value),
            max_turns=run_max_turns, budget=budget,
        )
        prompt = (
            f"You are the Oracle for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"## Instructions\n"
            f"Before outputting code or commands, write a `<thinking>` block analyzing the codebase against the spec.\n"
            f"Explicitly list any intentional design choices vs. real bugs, and determine your plan of action.\n"
            f"After thinking, complete the task requirements. Then write attestation.json to the submission directory:\n"
            f'  write(path="../submission/attestation.json", content=\'{{"task_id":"{task_id}","verdict":"pass","checklist":[]}}\')\n'
            f"Output DONE when complete."
        )
        turns = loop.run(prompt)
        phase = PhaseResult(phase="oracle", turns=turns)
        result.phases.append(phase)
        result.total_turns += len(turns)

    elif condition == AblationCondition.RESTRICTED:
        # Single agent with executor-only access (brief only).
        # Restricted runs lack oracle context, so verbose models (Anthropic) need
        # extra turns to converge — bump from default 20 to 30.
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
            max_turns=total_turns, budget=budget,  # single-role: may spend the whole run budget
        )
        prompt = (
            f"You are a Restricted agent for task: {task_id}\n\n"
            f"## Brief\n{brief_text}\n\n"
            f"## Instructions\n"
            f"Complete the task in the workspace. Then write attestation.json to the submission directory:\n"
            f'  write(path="../submission/attestation.json", content=\'{{"task_id":"{task_id}","verdict":"pass","checklist":[]}}\')\n'
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
            max_turns=phase_turns_2, budget=budget,
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
            max_turns=phase_turns_2, budget=budget,
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
            max_turns=phase_turns_2, budget=budget,
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
            max_turns=phase_turns_2, budget=budget,
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
            max_turns_per_phase=phase_turns_3,
            max_remediation_loops=max_remediation, budget=budget,
        )
        return orchestrator.run()

    elif condition in (
        AblationCondition.PROMPT_ONLY,
        AblationCondition.ENFORCED_SHARED_HISTORY,
        AblationCondition.ENFORCED,
    ):
        # role_enforcement_ablation experiment. See
        # experiments/role_enforcement_ablation/HYPOTHESIS.md for the design.
        # ENFORCED uses the variable orchestrator for audit parity with the other
        # two conditions (same code path, share_tools=share_history=False).
        from harness.orchestrator import VariableEnforcementOrchestrator
        share_tools = condition == AblationCondition.PROMPT_ONLY
        share_history = condition in (
            AblationCondition.PROMPT_ONLY,
            AblationCondition.ENFORCED_SHARED_HISTORY,
        )
        orch = VariableEnforcementOrchestrator(
            task_dir=task_dir,
            run_dir=run_dir,
            adapter=adapter,
            share_tools=share_tools,
            share_history=share_history,
            max_turns_per_phase=max_turns,
            max_remediation_loops=max_remediation, budget=budget,
        )
        return orch.run()

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
            max_remediation_loops=max_remediation, budget=budget,
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
            max_turns=max_turns, budget=budget,
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
            max_turns=15, budget=budget,
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
            max_turns=15, budget=budget,
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
            max_turns=max_turns, budget=budget,
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
            max_turns=15, budget=budget,
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
            max_turns=max_turns, budget=budget,
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

    elif condition == AblationCondition.ORACLE_COT:
        # Strong baseline: single oracle agent with chain-of-thought prompt
        # Gets 2x turns to match team compute budget (plan + execute internally)
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
            log_dir=os.path.join(logs, "oracle_cot"),
            max_turns=total_turns, budget=budget,  # single-role: may spend the whole run budget
        )
        prompt = (
            f"You are an expert Oracle agent for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"## Instructions\n"
            f"Follow this structured approach:\n\n"
            f"### Phase 1: Analysis & Planning (think step-by-step)\n"
            f"1. Read the spec carefully and identify ALL requirements.\n"
            f"2. Read workspace files to understand the current codebase state.\n"
            f"3. Create a mental plan: list each issue to fix, in priority order.\n"
            f"4. Identify potential pitfalls, edge cases, and dependencies.\n\n"
            f"### Phase 2: Implementation\n"
            f"5. Implement fixes one at a time, verifying each change.\n"
            f"6. Run tests after each significant change.\n"
            f"7. Cross-check your changes against ALL spec requirements.\n\n"
            f"### Phase 3: Self-Verification\n"
            f"8. Review your changes against the spec checklist.\n"
            f"9. Run final tests to confirm everything works.\n"
            f"10. Write attestation.json with verdict='pass'.\n\n"
            f'Write: write(path="attestation.json", content=\'{{"task_id":"{task_id}","verdict":"pass","checklist":[]}}\')\n'
            f"Output DONE when complete."
        )
        turns = loop.run(prompt)
        phase = PhaseResult(phase="oracle_cot", turns=turns)
        result.phases.append(phase)
        result.total_turns += len(turns)

    elif condition == AblationCondition.ORACLE_2PASS:
        # Strong baseline: two-pass oracle — first pass plans, second pass executes
        # Both passes are the SAME single agent with full access
        oracle_config = _make_oracle_config(
            spec_path=spec_path,
            workspace_dir=workspace,
            reports_dir=reports,
            messages_dir=messages,
            submission_dir=submission,
            task_dir=task_dir,
        )

        # Pass 1: Analysis and planning (write plan to file)
        loop1 = AgentLoop(
            role_config=oracle_config,
            adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "oracle_2pass_plan"),
            max_turns=max_turns, budget=budget,
        )
        plan_prompt = (
            f"You are an Oracle agent for task: {task_id} — PLANNING PASS\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"## Instructions\n"
            f"Your job in this pass is ONLY to analyze and plan. Do NOT implement yet.\n"
            f"1. Read the spec and all relevant workspace files.\n"
            f"2. Identify every issue, bug, or missing requirement.\n"
            f"3. Write a detailed plan to /workspace/plan.md with:\n"
            f"   - Each issue found (file, line, description)\n"
            f"   - The fix needed for each issue\n"
            f"   - Priority order for implementation\n"
            f"   - Potential risks or tricky areas\n"
            f'4. Use: write(path="plan.md", content="...your plan...")\n'
            f"5. Output DONE when your plan is written.\n\n"
            f"IMPORTANT: Do NOT modify any workspace code files. Only write plan.md."
        )
        turns1 = loop1.run(plan_prompt)
        phase1 = PhaseResult(phase="oracle_2pass_plan", turns=turns1)
        result.phases.append(phase1)
        result.total_turns += len(turns1)

        # Pass 2: Execute based on the plan
        loop2 = AgentLoop(
            role_config=oracle_config,
            adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "oracle_2pass_exec"),
            max_turns=max_turns, budget=budget,
        )
        exec_prompt = (
            f"You are an Oracle agent for task: {task_id} — EXECUTION PASS\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"## Instructions\n"
            f"A planning pass has already analyzed the task and written a plan.\n"
            f'1. Read the plan: read(path="plan.md")\n'
            f"2. Execute the plan step by step — implement all fixes.\n"
            f"3. Run tests to verify your changes.\n"
            f"4. Write attestation.json when all requirements are met.\n\n"
            f'write(path="attestation.json", content=\'{{"task_id":"{task_id}","verdict":"pass","checklist":[]}}\')\n'
            f"Output DONE when complete."
        )
        turns2 = loop2.run(exec_prompt)
        phase2 = PhaseResult(phase="oracle_2pass_exec", turns=turns2)
        result.phases.append(phase2)
        result.total_turns += len(turns2)

    # ================================================================
    # TOPOLOGY ABLATION — Different coordination patterns
    # ================================================================

    elif condition == AblationCondition.TOPO_ITERATIVE:
        # Iterative Planning: Planner <-> Executor alternate in rounds.
        # Planner proposes sub-plan, Executor implements & reports, Planner refines.
        # Mimics Cursor/Devin iterative planning loops.
        max_rounds = 3
        turns_per_round = max_turns // max_rounds  # ~6-7 turns per round

        for round_num in range(max_rounds):
            # --- Planner round ---
            planner_config = make_planner_config(
                spec_path=spec_path, messages_dir=messages, task_dir=task_dir,
            )
            planner_loop = AgentLoop(
                role_config=planner_config, adapter=adapter,
                messages_dir=messages,
                log_dir=os.path.join(logs, "planner", f"round_{round_num}"),
                max_turns=turns_per_round, budget=budget,
            )
            if round_num == 0:
                planner_prompt = (
                    f"You are the Planner for task: {task_id} (Round {round_num + 1}/{max_rounds})\n\n"
                    f"## Full Specification\n{spec_text}\n\n"
                    f"## Instructions\n"
                    f"Create a sub-plan for the FIRST set of changes needed.\n"
                    f"Focus on the highest-priority issues first.\n"
                    f"Send your sub-plan to the Executor via send_message(to='executor', content=...).\n"
                    f"Output DONE when done."
                )
            else:
                planner_prompt = (
                    f"You are the Planner for task: {task_id} (Round {round_num + 1}/{max_rounds})\n\n"
                    f"## Full Specification\n{spec_text}\n\n"
                    f"## Instructions\n"
                    f"Check messages from the Executor for their status report on previous work.\n"
                    f"Based on what they accomplished, create the NEXT sub-plan.\n"
                    f"Focus on remaining requirements not yet addressed.\n"
                    f"Send your sub-plan via send_message(to='executor', content=...).\n"
                    f"Output DONE when done."
                )
            planner_turns = planner_loop.run(planner_prompt)
            phase_p = PhaseResult(phase=f"planning_round_{round_num}", turns=planner_turns)
            result.phases.append(phase_p)
            result.total_turns += len(planner_turns)
            _relay_planner_text(planner_turns, messages)

            # --- Executor round ---
            executor_config = make_executor_config(
                brief_path=brief_path, workspace_dir=workspace, reports_dir=reports,
                messages_dir=messages, submission_dir=submission, task_dir=task_dir,
            )
            executor_loop = AgentLoop(
                role_config=executor_config, adapter=adapter,
                messages_dir=messages,
                log_dir=os.path.join(logs, "executor", f"round_{round_num}"),
                max_turns=turns_per_round, budget=budget,
            )
            is_final = round_num == max_rounds - 1
            executor_prompt = (
                f"You are the Executor for task: {task_id} (Round {round_num + 1}/{max_rounds})\n\n"
                f"## Brief\n{brief_text}\n\n"
                f"## Instructions\n"
                f"Check messages from the Planner for your current sub-plan.\n"
                f"Implement the changes described in the sub-plan.\n"
                + (
                    f"When done, send a status report to the Planner: "
                    f"send_message(to='planner', content='Status: <what you did, what remains>').\n"
                    if not is_final else
                    f"This is the FINAL round. Complete all remaining work.\n"
                )
                + f"Output DONE when done."
            )
            executor_turns = executor_loop.run(executor_prompt)
            phase_e = PhaseResult(phase=f"execution_round_{round_num}", turns=executor_turns)
            result.phases.append(phase_e)
            result.total_turns += len(executor_turns)

        # Final attestation — auto-write (no verifier in this topology)
        _write_passing_attestation(submission, task_id)

    elif condition == AblationCondition.TOPO_DUAL_EXEC:
        # Dual Executor: Planner -> 2 independent Executors -> Verifier selects best.
        # Mimics Codex/AlphaCode sample-and-filter approach.
        import shutil

        # Phase 1: Planning
        planner_config = make_planner_config(
            spec_path=spec_path, messages_dir=messages, task_dir=task_dir,
        )
        planner_loop = AgentLoop(
            role_config=planner_config, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "planner"),
            max_turns=max_turns, budget=budget,
        )
        planner_prompt = (
            f"You are the Planner for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"## Instructions\n"
            f"Create a detailed plan and send it to the Executor via send_message(to='executor', content=...).\n"
            f"Output DONE when done."
        )
        planner_turns = planner_loop.run(planner_prompt)
        phase1 = PhaseResult(phase="planning", turns=planner_turns)
        result.phases.append(phase1)
        result.total_turns += len(planner_turns)
        _relay_planner_text(planner_turns, messages)

        # Phase 2a: Executor A (original workspace)
        workspace_a = workspace  # original
        workspace_b = workspace + "_b"
        messages_b = messages + "_b"
        submission_b = submission + "_b"
        shutil.copytree(workspace, workspace_b)
        os.makedirs(messages_b, exist_ok=True)
        os.makedirs(submission_b, exist_ok=True)
        # Copy dialogue so Executor B also gets the plan
        dialogue_src = os.path.join(messages, "dialogue.jsonl")
        if os.path.exists(dialogue_src):
            shutil.copy2(dialogue_src, os.path.join(messages_b, "dialogue.jsonl"))

        half_turns = max_turns // 2  # each executor gets half the budget

        executor_config_a = make_executor_config(
            brief_path=brief_path, workspace_dir=workspace_a, reports_dir=reports,
            messages_dir=messages, submission_dir=submission, task_dir=task_dir,
        )
        exec_loop_a = AgentLoop(
            role_config=executor_config_a, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "executor_a"),
            max_turns=half_turns, budget=budget,
        )
        exec_prompt = (
            f"You are Executor A for task: {task_id}\n\n"
            f"## Brief\n{brief_text}\n\n"
            f"## Instructions\n"
            f"Check messages from the Planner, then implement the required changes.\n"
            f"Output DONE when done."
        )
        exec_a_turns = exec_loop_a.run(exec_prompt)
        phase2a = PhaseResult(phase="execution_a", turns=exec_a_turns)
        result.phases.append(phase2a)
        result.total_turns += len(exec_a_turns)

        # Phase 2b: Executor B (copied workspace)
        executor_config_b = make_executor_config(
            brief_path=brief_path, workspace_dir=workspace_b, reports_dir=reports,
            messages_dir=messages_b, submission_dir=submission_b, task_dir=task_dir,
        )
        exec_loop_b = AgentLoop(
            role_config=executor_config_b, adapter=adapter,
            messages_dir=messages_b,
            log_dir=os.path.join(logs, "executor_b"),
            max_turns=half_turns, budget=budget,
        )
        exec_b_turns = exec_loop_b.run(exec_prompt.replace("Executor A", "Executor B"))
        phase2b = PhaseResult(phase="execution_b", turns=exec_b_turns)
        result.phases.append(phase2b)
        result.total_turns += len(exec_b_turns)

        # Phase 3: Verifier compares both workspaces and selects best
        verifier_config = make_verifier_config(
            spec_path=spec_path, workspace_dir=workspace_a, reports_dir=reports,
            messages_dir=messages, submission_dir=submission, task_dir=task_dir,
        )
        verifier_loop = AgentLoop(
            role_config=verifier_config, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "verifier"),
            max_turns=max_turns, budget=budget,
        )
        verifier_prompt = (
            f"You are the Verifier for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"## Instructions\n"
            f"Two executors independently implemented fixes.\n"
            f"Workspace A is at the default workspace path.\n"
            f"Verify the workspace against the specification requirements.\n"
            f"Write attestation.json with verdict='pass' if requirements are met.\n"
            f"Output DONE when done."
        )
        verifier_turns = verifier_loop.run(verifier_prompt)
        phase3 = PhaseResult(phase="verification_a", turns=verifier_turns)
        result.phases.append(phase3)
        result.total_turns += len(verifier_turns)

        # If workspace A failed, try workspace B
        att_a = os.path.join(submission, "attestation.json")
        verdict_a = "fail"
        try:
            with open(att_a) as f:
                verdict_a = json.load(f).get("verdict", "fail")
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        if verdict_a != "pass":
            # Swap workspace B into place and verify
            shutil.rmtree(workspace_a)
            shutil.move(workspace_b, workspace_a)
            # Clear old attestation
            if os.path.exists(att_a):
                os.remove(att_a)

            verifier_loop_b = AgentLoop(
                role_config=verifier_config, adapter=adapter,
                messages_dir=messages,
                log_dir=os.path.join(logs, "verifier_b"),
                max_turns=max_turns, budget=budget,
            )
            verifier_b_turns = verifier_loop_b.run(verifier_prompt)
            phase3b = PhaseResult(phase="verification_b", turns=verifier_b_turns)
            result.phases.append(phase3b)
            result.total_turns += len(verifier_b_turns)

    elif condition == AblationCondition.TOPO_VERIFY_FIRST:
        # Verify-First: Verifier pre-analyzes workspace gaps, then Executor fixes.
        # Grounded gap analysis replaces abstract planning.

        # Phase 1: Verifier reads spec + workspace, produces gap analysis
        verifier_config = make_verifier_config(
            spec_path=spec_path, workspace_dir=workspace, reports_dir=reports,
            messages_dir=messages, submission_dir=submission, task_dir=task_dir,
        )
        gap_loop = AgentLoop(
            role_config=verifier_config, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "verifier_gap_analysis"),
            max_turns=max_turns, budget=budget,
        )
        gap_prompt = (
            f"You are the Gap Analyst for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"## Instructions\n"
            f"Your job is to ANALYZE, not to fix. Do NOT write attestation.json yet.\n"
            f"1. Read the specification carefully.\n"
            f"2. Examine the workspace files to understand the current codebase state.\n"
            f"3. For EACH spec requirement, check whether it is currently satisfied.\n"
            f"4. Create a GAP REPORT listing:\n"
            f"   - Which requirements are NOT met\n"
            f"   - The specific file(s) and line(s) where issues exist\n"
            f"   - What exact change is needed to fix each gap\n"
            f"5. Send this gap report to the Executor:\n"
            f"   send_message(to='executor', content='<your gap report>')\n"
            f"6. Output DONE when done.\n\n"
            f"IMPORTANT: Be specific and actionable. The Executor cannot see the spec."
        )
        gap_turns = gap_loop.run(gap_prompt)
        phase1 = PhaseResult(phase="gap_analysis", turns=gap_turns)
        result.phases.append(phase1)
        result.total_turns += len(gap_turns)
        _relay_planner_text(gap_turns, messages)  # relay if forgot send_message

        # Phase 2: Executor fixes the identified gaps
        executor_config = make_executor_config(
            brief_path=brief_path, workspace_dir=workspace, reports_dir=reports,
            messages_dir=messages, submission_dir=submission, task_dir=task_dir,
        )
        executor_loop = AgentLoop(
            role_config=executor_config, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "executor"),
            max_turns=max_turns, budget=budget,
        )
        executor_prompt = (
            f"You are the Executor for task: {task_id}\n\n"
            f"## Brief\n{brief_text}\n\n"
            f"## Instructions\n"
            f"A Gap Analyst has examined the workspace and identified specific issues.\n"
            f"Check messages for their detailed gap report.\n"
            f"Fix each identified gap in the workspace.\n"
            f"Output DONE when done."
        )
        executor_turns = executor_loop.run(executor_prompt)
        phase2 = PhaseResult(phase="execution", turns=executor_turns)
        result.phases.append(phase2)
        result.total_turns += len(executor_turns)

        # Phase 3: Verifier does final check and writes attestation
        verifier_loop2 = AgentLoop(
            role_config=verifier_config, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "verifier_final"),
            max_turns=max_turns, budget=budget,
        )
        verifier_prompt = (
            f"You are the Verifier for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"## Instructions\n"
            f"The Executor has fixed the previously identified gaps.\n"
            f"Verify the workspace against ALL spec requirements.\n"
            f"Write attestation.json with your verdict.\n"
            f"Output DONE when done."
        )
        verifier_turns = verifier_loop2.run(verifier_prompt)
        phase3 = PhaseResult(phase="verification", turns=verifier_turns)
        result.phases.append(phase3)
        result.total_turns += len(verifier_turns)

    elif condition == AblationCondition.TOPO_SELF_CHECK:
        # Self-Check: Single agent with structured implement -> self-verify -> fix protocol.
        # Control condition testing whether structured prompting captures multi-agent value.
        # Uses oracle config (full spec + workspace access) with explicit phase discipline.
        oracle_config = _make_oracle_config(
            spec_path=spec_path, workspace_dir=workspace, reports_dir=reports,
            messages_dir=messages, submission_dir=submission, task_dir=task_dir,
        )
        loop = AgentLoop(
            role_config=oracle_config, adapter=adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "self_check"),
            max_turns=total_turns, budget=budget,  # single-role: may spend the whole run budget
        )
        prompt = (
            f"You are a Self-Checking agent for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"## MANDATORY 3-PHASE PROTOCOL\n"
            f"You MUST follow these phases in strict order.\n\n"
            f"### PHASE 1: IMPLEMENT (use ~40% of your turns)\n"
            f"1. Read the spec and identify ALL requirements.\n"
            f"2. Read workspace files to understand current state.\n"
            f"3. Implement all necessary changes to satisfy the spec.\n"
            f"4. Run tests if available.\n\n"
            f"### PHASE 2: SELF-VERIFY (use ~30% of your turns)\n"
            f"STOP implementing. Switch to verification mode.\n"
            f"5. Re-read the FULL specification above.\n"
            f"6. For EACH requirement in the spec:\n"
            f"   a. Read the relevant workspace file(s)\n"
            f"   b. Check if the requirement is satisfied\n"
            f"   c. Note any gaps or issues found\n"
            f"7. Create a checklist of remaining issues.\n\n"
            f"### PHASE 3: FIX & FINALIZE (use ~30% of your turns)\n"
            f"8. Fix each issue found in Phase 2.\n"
            f"9. Re-verify the fixes.\n"
            f"10. Write attestation.json:\n"
            f'    write(path="attestation.json", content=\'{{"task_id":"{task_id}","verdict":"pass","checklist":[]}}\')\n\n'
            f"CRITICAL: Do NOT write attestation.json until you have completed Phase 2.\n"
            f"Output DONE when complete."
        )
        turns = loop.run(prompt)
        phase = PhaseResult(phase="self_check", turns=turns)
        result.phases.append(phase)
        result.total_turns += len(turns)

    elif condition == AblationCondition.HETERO:
        # Heterogeneous team: Planner + Executor + Verifier each use a different model.
        # Falls back to the single adapter for any role not specified in model_config.
        import time as _time
        from harness.adapters import create_adapter

        mc = model_config or {}

        def _role_adapter(role: str) -> ToolCallAdapter:
            if role in mc:
                return create_adapter(model=mc[role], temperature=0.2)
            return adapter

        planner_adapter = _role_adapter("planner")
        executor_adapter = _role_adapter("executor")
        verifier_adapter = _role_adapter("verifier")

        def _capture_role_usage(role: str, adpt: Any, wall_sec: float) -> None:
            try:
                usage = adpt.get_usage() if hasattr(adpt, "get_usage") else {}
            except Exception:
                usage = {}
            result.role_usage[role] = {
                "input_tokens": int(usage.get("input_tokens") or 0),
                "output_tokens": int(usage.get("output_tokens") or 0),
                "model": mc.get(role) or usage.get("model") or "unknown",
                "wall_sec": round(wall_sec, 2),
            }

        planner_config = make_planner_config(
            spec_path=spec_path, messages_dir=messages, task_dir=task_dir,
        )
        planner_loop = AgentLoop(
            role_config=planner_config, adapter=planner_adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "planner"),
            max_turns=max_turns, budget=budget,
        )
        planner_prompt = (
            f"You are the Planner for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"## Instructions\n"
            f"Create a plan and send it to the Executor via send_message(to='executor', content=...).\n"
            f"Output DONE when done."
        )
        _t0 = _time.time()
        planner_turns = planner_loop.run(planner_prompt)
        _capture_role_usage("planner", planner_adapter, _time.time() - _t0)
        phase1 = PhaseResult(phase="planning", turns=planner_turns)
        result.phases.append(phase1)
        result.total_turns += len(planner_turns)
        _relay_planner_text(planner_turns, messages)

        executor_config = make_executor_config(
            brief_path=brief_path, workspace_dir=workspace, reports_dir=reports,
            messages_dir=messages, submission_dir=submission, task_dir=task_dir,
        )
        executor_loop = AgentLoop(
            role_config=executor_config, adapter=executor_adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "executor"),
            max_turns=max_turns, budget=budget,
        )
        executor_prompt = (
            f"You are the Executor for task: {task_id}\n\n"
            f"## Brief\n{brief_text}\n\n"
            f"## Instructions\n"
            f"Check messages from the Planner, then complete the task.\n"
            f"Send a completion message to the Verifier when done.\n"
            f"Output DONE when done."
        )
        _t0 = _time.time()
        executor_turns = executor_loop.run(executor_prompt)
        _capture_role_usage("executor", executor_adapter, _time.time() - _t0)
        phase2 = PhaseResult(phase="execution", turns=executor_turns)
        result.phases.append(phase2)
        result.total_turns += len(executor_turns)

        verifier_config = make_verifier_config(
            spec_path=spec_path, workspace_dir=workspace, reports_dir=reports,
            messages_dir=messages, submission_dir=submission, task_dir=task_dir,
        )
        verifier_loop = AgentLoop(
            role_config=verifier_config, adapter=verifier_adapter,
            messages_dir=messages,
            log_dir=os.path.join(logs, "verifier", "attempt_0"),
            max_turns=max_turns, budget=budget,
        )
        verifier_prompt = (
            f"You are the Verifier for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"## Instructions\n"
            f"Verify the workspace against the spec. Write attestation.json.\n"
            f"Output DONE when done."
        )
        _t0 = _time.time()
        verifier_turns = verifier_loop.run(verifier_prompt)
        _capture_role_usage("verifier", verifier_adapter, _time.time() - _t0)
        phase3 = PhaseResult(phase="verification_0", turns=verifier_turns)
        result.phases.append(phase3)
        result.total_turns += len(verifier_turns)

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
    model_config: Optional[dict] = None,
    total_turns: int = 60,
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

    # Experiment-scoped conditions are excluded from the "all conditions" default
    # so that pre-existing ablation pipelines (which may omit the `conditions`
    # argument) do not accidentally run or double-count them. Callers who want
    # these conditions must request them explicitly.
    _EXPERIMENT_SCOPED = {
        AblationCondition.PROMPT_ONLY,
        AblationCondition.ENFORCED_SHARED_HISTORY,
        AblationCondition.ENFORCED,   # alias for FULL; would double-count otherwise
    }
    conditions = (
        conditions
        if conditions is not None
        else [c for c in AblationCondition if c not in _EXPERIMENT_SCOPED]
    )

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

    # Run directories go to local disk when TEAMBENCH_RUNS_DIR is set. Two
    # reasons, both measured: the docker sandbox cannot bind-mount anything
    # under this repository (NFS exported with root_squash, so the daemon's
    # mkdir is denied), and staging a full upstream checkout onto NFS is far
    # slower than onto local disk.
    runs_base = os.environ.get("TEAMBENCH_RUNS_DIR") or \
        os.path.join(os.path.dirname(output), "ablation_runs")
    os.makedirs(runs_base, exist_ok=True)

    # --- Resume: scan existing run dirs for completed (condition, task, seed) ---
    # Checkpoint is append-only and may contain multiple entries per key (e.g.
    # original + regrade patches). Keep only the LAST entry per key for metrics.
    checkpoint_path = output + ".checkpoint.jsonl"
    completed_keys: set[str] = set()
    if os.path.isfile(checkpoint_path):
        latest_by_key: dict[str, dict] = {}
        with open(checkpoint_path, "r") as cpf:
            for line in cpf:
                try:
                    entry = json.loads(line.strip())
                    key = f"{entry['condition']}:{entry['task_id']}:{entry['seed']}"
                    latest_by_key[key] = entry  # later writes override earlier
                except (json.JSONDecodeError, KeyError, ValueError):
                    pass
        for key, entry in latest_by_key.items():
            try:
                completed_keys.add(key)
                all_runs.append(entry)
                cond_enum = AblationCondition(entry["condition"])
                condition_scores[cond_enum].append(bool(entry.get("pass", False)))
                condition_partial[cond_enum].append(float(entry.get("partial_score", 0.0)))
            except (KeyError, ValueError):
                pass
        print(f"  Resumed {len(completed_keys)} completed runs from checkpoint")

    total = len(conditions) * len(task_names) * len(seeds)
    i = 0

    for condition in conditions:
        for task_name in task_names:
            for seed in seeds:
                i += 1
                run_key = f"{condition.value}:{task_name}:{seed}"
                if run_key in completed_keys:
                    print(f"\n[{i}/{total}] {condition.value} x {task_name} (seed={seed}) SKIPPED (checkpoint)")
                    continue

                print(f"\n[{i}/{total}] {condition.value} x {task_name} (seed={seed})")
                start_time = time.time()

                run_record = AblationRun(
                    condition=condition,
                    task_id=task_name,
                    seed=seed,
                )
                usage_before = _usage_snapshot(adapter)

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
                        model_config=model_config if condition == AblationCondition.HETERO else None, total_turns=total_turns,
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
                    # A rejected credential never heals inside a sweep. Left to
                    # continue, the loop records every remaining task as a
                    # zero-score run that is indistinguishable from a genuine
                    # failure once aggregated, and the final JSON then makes the
                    # cell look complete so a rerun skips it. That happened: a
                    # revoked key turned 68 of 144 claude-sonnet-5 runs into
                    # fake zeros. Stop at the first one instead.
                    if _is_credential_failure(e):
                        durable_append(checkpoint_path, json.dumps({
                                "condition": condition.value,
                                "task_id": task_name, "seed": seed,
                                "pass": False, "partial_score": 0.0,
                                "error": str(e), "checks": [],
                                "usage": _usage_delta(adapter, usage_before),
                                "aborted_sweep": True,
                            }) + "\n")
                        raise CredentialFailure(
                            "provider rejected the credential on %s x %s; "
                            "aborting so the remaining runs are not recorded "
                            "as fake zeros. Fix the key, delete any partially "
                            "written output JSON for this cell, and rerun.\n"
                            "  underlying error: %s"
                            % (condition.value, task_name, e)) from e

                partial_score = run_record.score.get("secondary", {}).get(
                    "partial_score", 1.0 if run_record.passed else 0.0
                )
                run_entry = {
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
                    # The per-check results, not just the aggregate. Without
                    # them a completed campaign can only ever be read on the
                    # guard-inflated scale: 303 of 374 checks across the
                    # verified core pass on an untouched workspace, so the
                    # do-nothing floor for partial_score is 0.815 and every
                    # condition is compressed against it. Recovering the
                    # checklist afterwards means re-reading run directories
                    # that may already have been cleaned up, which is how the
                    # previous sweep became unrescorable.
                    "checks": ((run_record.score.get("secondary") or {}).get("checks")
                               or run_record.score.get("checklist") or []),
                    # Token spend for this run alone. Turn-matching is the
                    # paper's claim; this is what lets the claim be checked on
                    # the other axis of compute rather than asserted.
                    "usage": _usage_delta(adapter, usage_before),
                }
                all_runs.append(run_entry)

                # --- Checkpoint: append completed run ---
                durable_append(checkpoint_path, json.dumps(run_entry) + "\n")

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
