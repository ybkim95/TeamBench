"""
TeamBench Agent Driver Interface.

Any LLM (OpenAI, Gemini, Claude, OSS) can be plugged in by implementing ModelAdapter.
RoleAgent wraps a ModelAdapter with role-specific constraints and tool access.

This is the standard contract for running automated evaluations.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import json
import os
import subprocess


class ModelAdapter(ABC):
    """
    Minimal interface for any LLM backend.
    Implement this for OpenAI, Anthropic, Google, vLLM, etc.
    """

    @abstractmethod
    def generate(self, messages: list[dict], **kwargs) -> str:
        """
        Args:
            messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
        Returns:
            Assistant response text.
        """
        raise NotImplementedError


@dataclass
class ToolResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0


class Tool(ABC):
    """Base class for tools available to agents."""
    name: str

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        raise NotImplementedError


class RunCommandTool(Tool):
    """Execute a shell command in the workspace."""
    name = "run"

    def __init__(self, cwd: str, allowed: bool = True):
        self.cwd = cwd
        self.allowed = allowed

    def execute(self, cmd: str, **kwargs) -> ToolResult:
        if not self.allowed:
            return ToolResult(stderr="Permission denied: this role cannot execute commands.", exit_code=1)
        try:
            res = subprocess.run(
                cmd, shell=True, cwd=self.cwd,
                text=True, capture_output=True, timeout=60,
            )
            return ToolResult(stdout=res.stdout, stderr=res.stderr, exit_code=res.returncode)
        except subprocess.TimeoutExpired:
            return ToolResult(stderr="Command timed out (60s).", exit_code=124)


class ReadFileTool(Tool):
    """Read a file from an allowed path."""
    name = "read"

    def __init__(self, allowed_roots: list[str], path_map: dict[str, str] | None = None, base_dir: str = ""):
        self.allowed_roots = [os.path.abspath(r) for r in allowed_roots]
        self.path_map = path_map or {}
        self.base_dir = os.path.abspath(base_dir) if base_dir else self.allowed_roots[0]

    def _resolve(self, path: str) -> str:
        # Apply path mapping (e.g., /shared/workspace -> actual run dir)
        for prefix, replacement in self.path_map.items():
            if path.startswith(prefix):
                return os.path.join(replacement, path[len(prefix):].lstrip("/"))
        # Resolve relative paths against base_dir
        if not os.path.isabs(path):
            return os.path.join(self.base_dir, path)
        return os.path.abspath(path)

    def execute(self, path: str, **kwargs) -> ToolResult:
        abs_path = self._resolve(path)
        if not any(abs_path.startswith(root) for root in self.allowed_roots):
            return ToolResult(stderr=f"Permission denied: cannot read {path}", exit_code=1)
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                return ToolResult(stdout=f.read())
        except Exception as e:
            return ToolResult(stderr=str(e), exit_code=1)


class WriteFileTool(Tool):
    """Write a file to an allowed path."""
    name = "write"

    def __init__(self, allowed_roots: list[str], path_map: dict[str, str] | None = None, base_dir: str = ""):
        self.allowed_roots = [os.path.abspath(r) for r in allowed_roots]
        self.path_map = path_map or {}
        self.base_dir = os.path.abspath(base_dir) if base_dir else self.allowed_roots[0]

    def _resolve(self, path: str) -> str:
        for prefix, replacement in self.path_map.items():
            if path.startswith(prefix):
                return os.path.join(replacement, path[len(prefix):].lstrip("/"))
        if not os.path.isabs(path):
            return os.path.join(self.base_dir, path)
        return os.path.abspath(path)

    def execute(self, path: str, content: str, **kwargs) -> ToolResult:
        abs_path = self._resolve(path)
        if not any(abs_path.startswith(root) for root in self.allowed_roots):
            return ToolResult(stderr=f"Permission denied: cannot write {path}", exit_code=1)
        try:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(stdout=f"Written {len(content)} bytes to {path}")
        except Exception as e:
            return ToolResult(stderr=str(e), exit_code=1)


class SendMessageTool(Tool):
    """Send a message to another role via the shared message log."""
    name = "send_message"

    def __init__(self, messages_dir: str, sender_role: str):
        self.messages_dir = messages_dir
        self.sender_role = sender_role

    def execute(self, to: str, content: str, **kwargs) -> ToolResult:
        from datetime import datetime, timezone
        msg = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "role": self.sender_role,
            "type": "message",
            "to": to,
            "content": content,
        }
        log_path = os.path.join(self.messages_dir, "dialogue.jsonl")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
        return ToolResult(stdout=f"Message sent to {to}")


@dataclass
class RoleConfig:
    """Configuration for a role agent's permissions and tools."""
    role: str  # planner | executor | verifier
    system_prompt: str
    tools: list[Tool]


def _build_path_map(
    workspace_dir: str = "",
    reports_dir: str = "",
    messages_dir: str = "",
    submission_dir: str = "",
    task_dir: str = "",
) -> dict[str, str]:
    """Build Docker-path → actual-path mapping for non-Docker agent runs."""
    m: dict[str, str] = {}
    if workspace_dir:
        m["/shared/workspace/"] = os.path.abspath(workspace_dir)
        m["/shared/workspace"] = os.path.abspath(workspace_dir)
    if reports_dir:
        m["/shared/reports/"] = os.path.abspath(reports_dir)
        m["/shared/reports"] = os.path.abspath(reports_dir)
    if messages_dir:
        m["/shared/messages/"] = os.path.abspath(messages_dir)
        m["/shared/messages"] = os.path.abspath(messages_dir)
    if submission_dir:
        m["/shared/submission/"] = os.path.abspath(submission_dir)
        m["/shared/submission"] = os.path.abspath(submission_dir)
    if task_dir:
        m["/task/"] = os.path.abspath(task_dir)
        m["/task"] = os.path.abspath(task_dir)
    return m


def make_planner_config(
    spec_path: str,
    messages_dir: str,
    task_dir: str = "",
) -> RoleConfig:
    """Create Planner role config: can read spec, send messages, no execution."""
    if not task_dir:
        task_dir = os.path.dirname(spec_path)
    pm = _build_path_map(messages_dir=messages_dir, task_dir=task_dir)
    return RoleConfig(
        role="planner",
        system_prompt=(
            "You are the Planner. You have access to the full task specification.\n"
            "Your job is to understand the requirements, decompose the goal, and create a clear plan.\n"
            "You CANNOT execute commands or modify the workspace.\n"
            "You MUST communicate your plan to the Executor by calling the send_message tool.\n"
            "Do NOT just write the plan as text — you MUST use send_message(to='executor', content=...).\n"
            "Highlight hidden constraints and edge cases the Executor might miss."
        ),
        tools=[
            ReadFileTool(allowed_roots=[os.path.dirname(spec_path), messages_dir], path_map=pm),
            SendMessageTool(messages_dir=messages_dir, sender_role="planner"),
        ],
    )


def make_executor_config(
    brief_path: str,
    workspace_dir: str,
    reports_dir: str,
    messages_dir: str,
    submission_dir: str = "",
    task_dir: str = "",
) -> RoleConfig:
    """Create Executor role config: can execute, edit workspace, read brief only."""
    if not task_dir:
        task_dir = os.path.dirname(brief_path)
    pm = _build_path_map(
        workspace_dir=workspace_dir, reports_dir=reports_dir,
        messages_dir=messages_dir, submission_dir=submission_dir,
        task_dir=task_dir,
    )
    return RoleConfig(
        role="executor",
        system_prompt=(
            "You are the Executor. You can run commands and edit files in the workspace.\n"
            "You only have access to a brief summary of the task (not the full spec).\n"
            "Follow the Planner's instructions carefully.\n"
            "For file reads/writes, use paths relative to the workspace (e.g., 'app/main.py').\n"
            "When done with your work, send a message to the verifier and output DONE.\n"
            "Ask the Planner for clarification if requirements are unclear."
        ),
        tools=[
            RunCommandTool(cwd=workspace_dir, allowed=True),
            ReadFileTool(
                allowed_roots=[workspace_dir, reports_dir, messages_dir, os.path.dirname(brief_path)],
                path_map=pm,
            ),
            WriteFileTool(allowed_roots=[workspace_dir, reports_dir], path_map=pm),
            SendMessageTool(messages_dir=messages_dir, sender_role="executor"),
        ],
    )


def make_verifier_config(
    spec_path: str,
    workspace_dir: str,
    reports_dir: str,
    messages_dir: str,
    submission_dir: str,
    task_dir: str = "",
) -> RoleConfig:
    """Create Verifier role config: can read workspace/reports (read-only), write attestation."""
    if not task_dir:
        task_dir = os.path.dirname(spec_path)
    pm = _build_path_map(
        workspace_dir=workspace_dir, reports_dir=reports_dir,
        messages_dir=messages_dir, submission_dir=submission_dir,
        task_dir=task_dir,
    )
    return RoleConfig(
        role="verifier",
        system_prompt=(
            "You are the Verifier. You independently verify whether the task was completed correctly.\n"
            "You have read-only access to the workspace and reports.\n"
            "You have access to the full task specification for checking compliance.\n"
            "You CANNOT execute commands or modify the workspace.\n"
            "Your job: check every requirement, identify violations, and produce attestation.json.\n"
            "Write attestation using: write(path='attestation.json', content=...)\n"
            "If requirements are not met, send feedback to the Executor and set verdict='fail'.\n"
            "Only set verdict='pass' when ALL requirements are satisfied.\n"
            "When done, output DONE."
        ),
        tools=[
            ReadFileTool(
                allowed_roots=[
                    os.path.dirname(spec_path), workspace_dir, reports_dir, messages_dir, submission_dir,
                ],
                path_map=pm,
                base_dir=workspace_dir,
            ),
            WriteFileTool(allowed_roots=[submission_dir], path_map=pm, base_dir=submission_dir),
            SendMessageTool(messages_dir=messages_dir, sender_role="verifier"),
        ],
    )
