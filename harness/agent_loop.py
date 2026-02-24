"""
Single-agent execution loop for TeamBench.

Runs one role (planner/executor/verifier) in a turn-based loop:
1. Poll for new messages from other agents
2. Call LLM with tools
3. Execute tool calls and feed results back
4. Stop when agent signals completion
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

from google.genai import types

from harness.agent_interface import RoleConfig, Tool, ToolResult
from harness.gemini_adapter import GeminiAdapter, tools_to_gemini_declarations


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


class AgentLoop:
    """Run a single agent role in a tool-calling loop."""

    def __init__(
        self,
        role_config: RoleConfig,
        adapter: GeminiAdapter,
        messages_dir: str,
        log_dir: str | None = None,
        max_turns: int = 30,
    ):
        self.config = role_config
        self.adapter = adapter
        self.messages_dir = messages_dir
        self.log_dir = log_dir or os.path.join("logs", role_config.role)
        self.max_turns = max_turns
        self._seen_msg_count = 0

    def run(self, initial_prompt: str) -> list[AgentTurn]:
        """Execute the agent loop. Returns list of turns."""
        gemini_tools = tools_to_gemini_declarations(self.config.tools)

        # Build initial contents
        contents: list[types.Content] = [
            types.Content(role="user", parts=[types.Part.from_text(text=initial_prompt)]),
        ]

        turns: list[AgentTurn] = []
        consecutive_no_tool = 0
        max_no_tool_turns = 3  # Break if stuck with no tool calls for N turns

        for turn_num in range(self.max_turns):
            turn = AgentTurn(turn=turn_num, role=self.config.role)

            # Poll for new messages
            new_msgs, self._seen_msg_count = _poll_messages(
                self.messages_dir, self.config.role, self._seen_msg_count,
            )
            if new_msgs:
                msg_text = "\n".join(
                    f"[Message from {m['role']}]: {m['content']}" for m in new_msgs
                )
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=f"New messages received:\n{msg_text}")],
                ))

            # Call LLM
            response = self.adapter.generate_with_tools(
                contents=contents,
                system_instruction=self.config.system_prompt,
                tools=gemini_tools,
            )

            # Process response parts
            has_function_call = False
            function_response_parts = []

            for candidate in response.candidates or []:
                if not candidate.content or not candidate.content.parts:
                    continue
                for part in candidate.content.parts:
                    # Text part
                    if part.text:
                        turn.text += part.text
                        # Check for done signal
                        if "DONE" in part.text or "TASK_COMPLETE" in part.text:
                            turn.done = True

                    # Function call part
                    if part.function_call:
                        has_function_call = True
                        fc = part.function_call
                        tool_name = fc.name
                        tool_args = dict(fc.args) if fc.args else {}

                        turn.tool_calls.append({"name": tool_name, "args": tool_args})

                        # Execute the tool
                        result = _execute_tool(tool_name, tool_args, self.config.tools)
                        result_dict = {
                            "stdout": _truncate(result.stdout, STDOUT_LIMIT),
                            "stderr": _truncate(result.stderr, STDERR_LIMIT),
                            "exit_code": result.exit_code,
                        }
                        turn.tool_results.append(result_dict)

                        # Build function response
                        function_response_parts.append(
                            types.Part.from_function_response(
                                name=tool_name,
                                response={
                                    "stdout": result_dict["stdout"],
                                    "stderr": result_dict["stderr"],
                                    "exit_code": result.exit_code,
                                },
                            )
                        )

            # Append model response to contents
            if response.candidates and response.candidates[0].content:
                contents.append(response.candidates[0].content)

            # If there were function calls, send results back
            if function_response_parts:
                contents.append(types.Content(role="user", parts=function_response_parts))

            # Log turn
            _log_turn(self.log_dir, self.config.role, turn)
            turns.append(turn)

            # Track consecutive turns with no tool calls (stuck detection)
            if len(turn.tool_calls) == 0:
                consecutive_no_tool += 1
            else:
                consecutive_no_tool = 0

            print(f"  [{self.config.role}] Turn {turn_num}: "
                  f"{len(turn.tool_calls)} tool calls, done={turn.done}")

            if turn.done:
                break

            # Break stuck loops: N consecutive turns with no tool calls
            if consecutive_no_tool >= max_no_tool_turns:
                print(f"  [{self.config.role}] Breaking: {max_no_tool_turns} turns with no tool calls")
                turn.done = True
                break

        return turns
