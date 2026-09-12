"""
Single-agent execution loop for TeamBench.

Runs one role (planner/executor/verifier) in a turn-based loop:
1. Poll for new messages from other agents
2. Call LLM with tools
3. Execute tool calls and feed results back
4. Stop when agent signals completion

Provider-agnostic: depends only on ToolCallAdapter and AdapterResponse.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

from harness.agent_interface import (
    AdapterResponse,
    RoleConfig,
    Tool,
    ToolCallAdapter,
    ToolResult,
    tools_to_standard_declarations,
)


STDOUT_LIMIT = 4000
STDERR_LIMIT = 2000


@dataclass
class AgentTurn:
    turn: int
    role: str
    text: str = ""
    tool_calls: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    done: bool = False


def _truncate(s: str, limit: int) -> str:
    if len(s) <= limit:
        return s
    return s[:limit] + f"\n... [truncated, {len(s)} chars total]"


def _poll_messages(messages_dir: str, role: str, seen_count: int) -> tuple[list[dict], int]:
    """Read new messages directed to this role from dialogue.jsonl."""
    log_path = os.path.join(messages_dir, "dialogue.jsonl")
    if not os.path.exists(log_path):
        return [], seen_count

    with open(log_path, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    new_messages = []
    for line in all_lines[seen_count:]:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            # Show messages TO this role or broadcast messages
            if msg.get("to", "") == role or msg.get("to", "") == "all":
                new_messages.append(msg)
        except json.JSONDecodeError:
            continue

    return new_messages, len(all_lines)


def _execute_tool(tool_name: str, tool_args: dict, tools: list[Tool]) -> ToolResult:
    """Find and execute a tool by name."""
    for tool in tools:
        if tool.name == tool_name:
            return tool.execute(**tool_args)
    return ToolResult(stderr=f"Unknown tool: {tool_name}", exit_code=1)


def _log_turn(log_dir: str, role: str, turn: AgentTurn) -> None:
    """Write turn data to a log file."""
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, f"turn_{turn.turn:03d}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(turn), f, indent=2, default=str)


class TurnBudget:
    """A total LLM-turn allowance shared across every phase of one run.

    Before this existed, each role got its own `max_turns`, so the conditions
    compared in the ablation ran at wildly different compute: Solo 20 turns,
    Restricted 30, the two-role teams 40, and Full Team up to 140 once the two
    remediation rounds are counted. Any Solo-versus-Team difference measured that
    way is confounded with a 7x compute gap. One TurnBudget is created per run and
    handed to every AgentLoop the condition builds, so all conditions spend from
    the same pool.
    """

    def __init__(self, total: int):
        self.total = int(total)
        self.used = 0

    def consume(self, n: int = 1) -> bool:
        """Take n turns. Returns False when the budget is exhausted."""
        if self.used + n > self.total:
            return False
        self.used += n
        return True

    @property
    def remaining(self) -> int:
        return max(0, self.total - self.used)

    def __repr__(self) -> str:
        return f"TurnBudget(used={self.used}/{self.total})"


class AgentLoop:
    """Run a single agent role in a tool-calling loop."""

    def __init__(
        self,
        role_config: RoleConfig,
        adapter: ToolCallAdapter,
        messages_dir: str,
        log_dir: str | None = None,
        max_turns: int = 30,
        lenient_mode: bool = False,
        budget: "TurnBudget | None" = None,
    ):
        self.config = role_config
        self.adapter = adapter
        self.messages_dir = messages_dir
        self.log_dir = log_dir or os.path.join("logs", role_config.role)
        self.max_turns = max_turns
        self.lenient_mode = lenient_mode
        self.budget = budget
        self._seen_msg_count = 0

    def run(
        self,
        initial_prompt: str,
        seed_context: Optional[list[dict]] = None,
    ) -> list[AgentTurn]:
        """Execute the agent loop. Returns list of turns.

        Args:
            initial_prompt: the first user message the agent receives.
            seed_context: optional list of {role, content} dicts prepended before
                `initial_prompt`. Used by the `enforced_shared_history` and
                `prompt_only` ablation conditions to expose prior-phase transcripts
                to the current role. Default None preserves baseline behavior for
                every existing caller — no regression risk.
        """
        std_tools = tools_to_standard_declarations(self.config.tools)

        # Conversation history as plain dicts. seed_context (if any) appears first
        # so the agent sees prior turns as context before receiving its own prompt.
        messages: list[dict] = []
        if seed_context:
            messages.extend(seed_context)
        messages.append({"role": "user", "content": initial_prompt})

        turns: list[AgentTurn] = []
        consecutive_no_tool = 0
        # Lenient mode gives open-source models more chances before giving up
        max_no_tool_turns = 5 if self.lenient_mode else 3
        recent_tool_signatures: list[str] = []  # Track repeated identical calls
        max_repeated_tool = 3  # Break if same tool+args repeated N times

        for turn_num in range(self.max_turns):
            # A run-level budget, when supplied, is authoritative over the per-phase
            # cap. Every ablation condition is constructed with one TurnBudget shared
            # across all of its phases, so a three-role team and a single agent spend
            # from the same pool and the Solo-vs-Team contrast is compute-matched.
            if self.budget is not None and not self.budget.consume():
                break
            turn = AgentTurn(turn=turn_num, role=self.config.role)

            # Poll for new messages
            new_msgs, self._seen_msg_count = _poll_messages(
                self.messages_dir, self.config.role, self._seen_msg_count,
            )
            if new_msgs:
                msg_text = "\n".join(
                    f"[Message from {m['role']}]: {m['content']}" for m in new_msgs
                )
                messages.append({
                    "role": "user",
                    "content": f"New messages received:\n{msg_text}",
                })

            # Call LLM via provider-agnostic interface
            response: AdapterResponse = self.adapter.generate_with_tools(
                messages=messages,
                system_prompt=self.config.system_prompt,
                tools=std_tools,
            )

            # Record assistant text
            if response.text:
                turn.text = response.text
                if "DONE" in response.text or "TASK_COMPLETE" in response.text:
                    turn.done = True

            # Append assistant message to history
            messages.append({"role": "assistant", "content": response.text or ""})

            # Process tool calls
            tool_result_parts: list[dict] = []
            for tc in response.tool_calls:
                tool_name = tc.get("name", "")
                tool_args = tc.get("args", {})

                turn.tool_calls.append({"name": tool_name, "args": tool_args})

                # Execute the tool
                result = _execute_tool(tool_name, tool_args, self.config.tools)
                result_dict = {
                    "stdout": _truncate(result.stdout, STDOUT_LIMIT),
                    "stderr": _truncate(result.stderr, STDERR_LIMIT),
                    "exit_code": result.exit_code,
                }
                turn.tool_results.append(result_dict)

                tool_result_parts.append({
                    "tool_name": tool_name,
                    "result": result_dict,
                })

            # Feed tool results back as a user message
            if tool_result_parts:
                result_text = "\n\n".join(
                    f"Tool '{p['tool_name']}' result:\n"
                    f"stdout: {p['result']['stdout']}\n"
                    f"stderr: {p['result']['stderr']}\n"
                    f"exit_code: {p['result']['exit_code']}"
                    for p in tool_result_parts
                )
                messages.append({"role": "user", "content": result_text})
            else:
                # Strict Anthropic models (e.g. Opus 4.7) require the
                # conversation to end with a user message. When the assistant
                # turn had no tool calls, inject a minimal continuation nudge.
                messages.append({
                    "role": "user",
                    "content": "Continue, or emit DONE / TASK_COMPLETE if finished.",
                })

            # Log turn
            _log_turn(self.log_dir, self.config.role, turn)
            turns.append(turn)

            # Track consecutive turns with no tool calls (stuck detection)
            if len(turn.tool_calls) == 0:
                consecutive_no_tool += 1
                # Lenient mode: nudge open-source models after 2 consecutive no-tool turns
                if self.lenient_mode and consecutive_no_tool == 2:
                    messages.append({
                        "role": "user",
                        "content": (
                            "If you want to use a tool, format your response as a JSON "
                            'tool call: {"name": "tool_name", "args": {...}}'
                        ),
                    })
            else:
                consecutive_no_tool = 0

            # Track repeated identical tool calls (read-loop detection)
            if turn.tool_calls:
                sig = json.dumps(
                    [{"name": tc["name"], "args": tc["args"]} for tc in turn.tool_calls],
                    sort_keys=True,
                )
                recent_tool_signatures.append(sig)
            else:
                recent_tool_signatures.append("")

            print(f"  [{self.config.role}] Turn {turn_num}: "
                  f"{len(turn.tool_calls)} tool calls, done={turn.done}")

            if turn.done:
                break

            # Break stuck loops: N consecutive turns with no tool calls
            if consecutive_no_tool >= max_no_tool_turns:
                print(f"  [{self.config.role}] Breaking: {max_no_tool_turns} turns with no tool calls")
                turn.done = True
                break

            # Break read loops: same tool+args repeated N times consecutively
            if len(recent_tool_signatures) >= max_repeated_tool:
                last_n = recent_tool_signatures[-max_repeated_tool:]
                if last_n[0] and all(s == last_n[0] for s in last_n):
                    # Nudge the agent to try a different approach
                    messages.append({
                        "role": "user",
                        "content": (
                            "WARNING: You have repeated the exact same tool call "
                            f"{max_repeated_tool} times. You appear to be stuck. "
                            "Try a DIFFERENT approach: modify the file, run a command, "
                            "or use a different tool. If you are done, output DONE."
                        ),
                    })
                    # Allow one more chance, then force-break on next repeat
                    max_repeated_tool += 2  # Raise threshold so nudge fires once

        return turns
