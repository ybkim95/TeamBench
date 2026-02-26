"""
OpenAI adapter for TeamBench agent driver.

Implements ToolCallAdapter using the `openai` Python SDK.
Supports GPT-4o, GPT-4-turbo, o1, o3, and other OpenAI chat models.

Requires: pip install openai
API key:  OPENAI_API_KEY environment variable
"""
from __future__ import annotations

import json
import os
from typing import Any

from harness.agent_interface import AdapterResponse, ToolCallAdapter


def _standard_to_openai_functions(tools: list[dict]) -> list[dict]:
    """Convert standard tool declarations to OpenAI function-calling format."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("parameters", {"type": "object", "properties": {}}),
            },
        }
        for t in tools
    ]


class OpenAIAdapter(ToolCallAdapter):
    """OpenAI GPT/o-series adapter for TeamBench.

    Uses the openai >= 1.0 SDK with the chat completions API and
    parallel function calling.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
        temperature: float = 0.2,
        max_tokens: int = 8192,
    ):
        try:
            import openai
        except ImportError as exc:
            raise ImportError(
                "The 'openai' package is required for OpenAIAdapter. "
                "Install it with: pip install openai"
            ) from exc

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._total_input_tokens = 0
        self._total_output_tokens = 0

        key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not key:
            raise ValueError(
                "OPENAI_API_KEY not set. Provide api_key or set the environment variable."
            )
        self._client = openai.OpenAI(api_key=key)

    # ------------------------------------------------------------------
    # ToolCallAdapter interface
    # ------------------------------------------------------------------

    def generate_with_tools(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: list[dict],
    ) -> AdapterResponse:
        """Call OpenAI chat completions with function calling and return AdapterResponse."""
        oai_messages = self._build_messages(messages, system_prompt)
        oai_tools = _standard_to_openai_functions(tools) if tools else None

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": oai_messages,
            "max_tokens": self.max_tokens,
        }
        # o-series reasoning models do not support temperature
        if not self.model.startswith(("o1", "o3", "o4")):
            kwargs["temperature"] = self.temperature
        if oai_tools:
            kwargs["tools"] = oai_tools
            kwargs["tool_choice"] = "auto"

        response = self._client.chat.completions.create(**kwargs)
        self._track_usage(response)
        return self._parse_response(response)

    def get_usage(self) -> dict:
        """Return cumulative token usage."""
        return {
            "input_tokens": self._total_input_tokens,
            "output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "model": self.model,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_messages(self, messages: list[dict], system_prompt: str) -> list[dict]:
        """Prepend system prompt and convert roles to OpenAI format."""
        oai: list[dict] = []
        if system_prompt:
            oai.append({"role": "system", "content": system_prompt})
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            # "tool" role in standard format -> "user" in OpenAI (results already formatted as text)
            if role == "tool":
                oai.append({"role": "user", "content": content})
            else:
                oai.append({"role": role, "content": content})
        return oai

    def _parse_response(self, response: Any) -> AdapterResponse:
        """Parse an OpenAI ChatCompletion into AdapterResponse."""
        text = ""
        tool_calls: list[dict] = []

        choice = response.choices[0] if response.choices else None
        if not choice:
            return AdapterResponse()

        msg = choice.message
        if msg.content:
            text = msg.content

        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError:
                    args = {"_raw": tc.function.arguments}
                tool_calls.append({"name": tc.function.name, "args": args})

        done = "DONE" in text or "TASK_COMPLETE" in text
        return AdapterResponse(text=text, tool_calls=tool_calls, done=done)

    def _track_usage(self, response: Any) -> None:
        """Accumulate token counts from response usage."""
        usage = getattr(response, "usage", None)
        if usage:
            self._total_input_tokens += getattr(usage, "prompt_tokens", 0) or 0
            self._total_output_tokens += getattr(usage, "completion_tokens", 0) or 0
