"""
Multi-agent orchestrator for TeamBench.

Implements the 3-phase sequential protocol:
1. Planning: Planner reads spec → sends plan to Executor
2. Execution: Executor reads brief + messages → fixes workspace → tells Verifier
3. Verification: Verifier reads spec + workspace → writes attestation
4. Remediation: If verdict=fail → Executor gets feedback → re-verify (max 2 loops)
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from harness.agent_interface import (
    make_planner_config,
    make_executor_config,
    make_verifier_config,
)
from harness.agent_loop import AgentLoop, AgentTurn
from harness.gemini_adapter import GeminiAdapter


@dataclass
class PhaseResult:
    phase: str
    turns: list[AgentTurn] = field(default_factory=list)
    success: bool = True


@dataclass
class OrchestratorResult:
    task_id: str
    phases: list[PhaseResult] = field(default_factory=list)
    verdict: str = "fail"
    remediation_loops: int = 0
    total_turns: int = 0


def _relay_planner_text(turns: list[AgentTurn], messages_dir: str) -> None:
    """If planner produced text but never called send_message, inject it as a message."""
    sent_any = any(
        tc.get("name") == "send_message"
        for t in turns
        for tc in t.tool_calls
    )
    if sent_any:
        return

    # Collect all planner text
    text = "\n".join(t.text for t in turns if t.text).strip()
    if not text:
        return

    # Remove trailing DONE markers
    for marker in ["DONE", "TASK_COMPLETE"]:
        if text.endswith(marker):
            text = text[: -len(marker)].strip()

    print("  [orchestrator] Planner did not use send_message — relaying text to executor")
    msg = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "role": "planner",
        "type": "message",
        "to": "executor",
        "content": text,
    }
    log_path = os.path.join(messages_dir, "dialogue.jsonl")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")


class TaskOrchestrator:
    """Coordinate Planner → Executor → Verifier for a single task."""

    def __init__(
        self,
        task_dir: str,
        run_dir: str,
        adapter: GeminiAdapter,
        max_turns_per_phase: int = 20,
        max_remediation_loops: int = 2,
    ):
        self.task_dir = task_dir
        self.run_dir = run_dir
        self.adapter = adapter
        self.max_turns_per_phase = max_turns_per_phase
        self.max_remediation_loops = max_remediation_loops

        # Run directories
        self.workspace = os.path.join(run_dir, "workspace")
        self.reports = os.path.join(run_dir, "reports")
        self.messages = os.path.join(run_dir, "messages")
        self.submission = os.path.join(run_dir, "submission")

        # Task files
        self.spec_path = os.path.join(task_dir, "spec.md")
        self.brief_path = os.path.join(task_dir, "brief.md")

    def run(self) -> OrchestratorResult:
        """Execute the full 3-phase protocol with remediation loop."""
        task_id = os.path.basename(self.task_dir)
        result = OrchestratorResult(task_id=task_id)

        # Read task files for prompts
        spec_text = self._read_file(self.spec_path)
        brief_text = self._read_file(self.brief_path)

        # === Phase 1: Planning ===
        print(f"\n{'='*50}")
        print(f"  PHASE 1: PLANNING")
        print(f"{'='*50}")

        planner_config = make_planner_config(
            spec_path=self.spec_path,
            messages_dir=self.messages,
            task_dir=self.task_dir,
        )
        planner_loop = AgentLoop(
            role_config=planner_config,
            adapter=self.adapter,
            messages_dir=self.messages,
            log_dir=os.path.join(self.run_dir, "logs", "planner"),
            max_turns=self.max_turns_per_phase,
        )

        planner_prompt = (
            f"You are the Planner for task: {task_id}\n\n"
            f"## Full Specification\n{spec_text}\n\n"
            f"## Instructions\n"
            f"1. Read and understand all requirements in the specification.\n"
            f"2. Create a detailed plan for the Executor.\n"
            f"3. IMPORTANT: Send the plan to the Executor by calling: "
            f"send_message(to='executor', content='<your detailed plan>')\n"
            f"4. Include ALL specific requirements, exact values, edge cases, and constraints.\n"
            f"5. The Executor only has a brief summary — they need YOUR detailed instructions.\n"
            f"6. When done sending the plan, output DONE."
        )

        planner_turns = planner_loop.run(planner_prompt)
        phase1 = PhaseResult(phase="planning", turns=planner_turns)
        result.phases.append(phase1)
        result.total_turns += len(planner_turns)

        # Safety: relay planner text as message if it forgot to use send_message
        _relay_planner_text(planner_turns, self.messages)

        # === Phase 2: Execution ===
        print(f"\n{'='*50}")
        print(f"  PHASE 2: EXECUTION")
        print(f"{'='*50}")

        executor_config = make_executor_config(
            brief_path=self.brief_path,
            workspace_dir=self.workspace,
            reports_dir=self.reports,
            messages_dir=self.messages,
            submission_dir=self.submission,
            task_dir=self.task_dir,
        )
        executor_loop = AgentLoop(
            role_config=executor_config,
            adapter=self.adapter,
            messages_dir=self.messages,
            log_dir=os.path.join(self.run_dir, "logs", "executor"),
            max_turns=self.max_turns_per_phase,
        )

        executor_prompt = (
            f"You are the Executor for task: {task_id}\n\n"
            f"## Brief\n{brief_text}\n\n"
            f"## Instructions\n"
            f"1. Check messages from the Planner for detailed instructions.\n"
            f"2. Explore the workspace using run(cmd='ls -R') or read(path='<relative_path>').\n"
            f"3. Use relative paths for files (e.g., read(path='app/main.py')).\n"
            f"4. Follow the Planner's instructions to fix the code/config.\n"
            f"5. Write files using write(path='<relative_path>', content='...').\n"
            f"6. Run tests or validation using run(cmd='...').\n"
            f"7. Send a completion message to the Verifier: "
            f"send_message(to='verifier', content='Work complete.').\n"
            f"8. When done, output DONE."
        )

        executor_turns = executor_loop.run(executor_prompt)
        phase2 = PhaseResult(phase="execution", turns=executor_turns)
        result.phases.append(phase2)
        result.total_turns += len(executor_turns)

        # === Phase 3: Verification + Remediation Loop ===
        for loop_num in range(self.max_remediation_loops + 1):
            print(f"\n{'='*50}")
            print(f"  PHASE 3: VERIFICATION (attempt {loop_num + 1})")
            print(f"{'='*50}")

            verifier_config = make_verifier_config(
                spec_path=self.spec_path,
                workspace_dir=self.workspace,
                reports_dir=self.reports,
                messages_dir=self.messages,
                submission_dir=self.submission,
                task_dir=self.task_dir,
            )
            verifier_loop = AgentLoop(
                role_config=verifier_config,
                adapter=self.adapter,
                messages_dir=self.messages,
                log_dir=os.path.join(self.run_dir, "logs", "verifier", f"attempt_{loop_num}"),
                max_turns=self.max_turns_per_phase,
            )

            verifier_prompt = (
                f"You are the Verifier for task: {task_id}\n\n"
                f"## Full Specification\n{spec_text}\n\n"
                f"## Instructions\n"
                f"1. Read the specification carefully.\n"
                f"2. Check the workspace files to verify all requirements are met.\n"
                f"   Use read(path='app/main.py') etc. with relative paths to workspace.\n"
                f"3. For EACH requirement, verify compliance.\n"
                f"4. Write attestation.json. IMPORTANT: The content MUST be valid JSON.\n"
                f"   Do NOT use quotes or special characters inside note strings.\n"
                f"   Example:\n"
                f"   write(path='attestation.json', content='{{"
                f"\"task_id\":\"{task_id}\","
                f"\"verdict\":\"pass\","
                f"\"checklist\":["
                f"{{\"id\":\"req_1\",\"ok\":true,\"note\":\"requirement met\"}},"
                f"{{\"id\":\"req_2\",\"ok\":true,\"note\":\"verified correct\"}}"
                f"]}}')\n"
                f"5. If verdict is 'fail', send feedback to executor via send_message.\n"
                f"6. Output DONE when finished."
            )

            verifier_turns = verifier_loop.run(verifier_prompt)
            phase3 = PhaseResult(phase=f"verification_{loop_num}", turns=verifier_turns)
            result.phases.append(phase3)
            result.total_turns += len(verifier_turns)

            # Check attestation
            verdict = self._check_attestation()
            if verdict == "pass":
                result.verdict = "pass"
                result.remediation_loops = loop_num
                print(f"\n  VERDICT: PASS (after {loop_num} remediation loops)")
                return result

            # If fail and we have remediation attempts left
            if loop_num < self.max_remediation_loops:
                print(f"\n  VERDICT: FAIL — starting remediation loop {loop_num + 1}")
                result.remediation_loops = loop_num + 1

                # Re-run executor with feedback
                executor_loop2 = AgentLoop(
                    role_config=executor_config,
                    adapter=self.adapter,
                    messages_dir=self.messages,
                    log_dir=os.path.join(self.run_dir, "logs", "executor", f"remediation_{loop_num}"),
                    max_turns=self.max_turns_per_phase,
                )

                remediation_prompt = (
                    f"You are the Executor for task: {task_id}\n\n"
                    f"## Brief\n{brief_text}\n\n"
                    f"## Instructions\n"
                    f"The Verifier found issues with your work. Check messages for feedback.\n"
                    f"Use relative paths for file reads/writes (e.g., 'app/main.py').\n"
                    f"Fix the issues and notify the Verifier when done.\n"
                    f"Output DONE when finished."
                )

                executor_turns2 = executor_loop2.run(remediation_prompt)
                phase_fix = PhaseResult(phase=f"remediation_{loop_num}", turns=executor_turns2)
                result.phases.append(phase_fix)
                result.total_turns += len(executor_turns2)

        print(f"\n  FINAL VERDICT: FAIL (exhausted {self.max_remediation_loops} remediation attempts)")
        return result

    def _read_file(self, path: str) -> str:
        """Read a text file, return empty string if missing."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def _check_attestation(self) -> str:
        """Check attestation.json verdict. Returns 'pass', 'fail', or 'missing'."""
        att_path = os.path.join(self.submission, "attestation.json")
        try:
            with open(att_path, "r", encoding="utf-8") as f:
                raw = f.read()
        except FileNotFoundError:
            return "missing"

        # Try direct parse
        try:
            att = json.loads(raw)
            return att.get("verdict", "fail")
        except json.JSONDecodeError:
            pass

        # Attempt repair: extract verdict via regex
        import re
        m = re.search(r'"verdict"\s*:\s*"(pass|fail)"', raw)
        if m:
            verdict = m.group(1)
            print(f"  [orchestrator] Repaired invalid attestation JSON, verdict={verdict}")
            # Rewrite a clean attestation
            clean = {"task_id": os.path.basename(self.task_dir), "verdict": verdict, "checklist": []}
            with open(att_path, "w", encoding="utf-8") as f:
                json.dump(clean, f)
            return verdict

        return "missing"
