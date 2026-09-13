"""
Anthropic adapter for TeamBench agent driver.

Implements ToolCallAdapter using the `anthropic` Python SDK.
Supports Claude 3 Opus/Sonnet/Haiku and claude-* model identifiers.

Requires: pip install anthropic
API key:  ANTHROPIC_API_KEY environment variable
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any


def _load_key_from_dotenv(key_name: str) -> str:
    for p in [".env", os.path.join(os.path.dirname(__file__), "..", "..", ".env")]:
        if os.path.exists(p):
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(key_name) and "=" in line:
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""

from harness.agent_interface import AdapterResponse, ToolCallAdapter

logger = logging.getLogger(__name__)


def _standard_to_anthropic_tools(tools: list[dict]) -> list[dict]:
    """Convert standard tool declarations to Anthropic tool format."""
    return [
        {
            "name": t["name"],
            "description": t.get("description", ""),
            "input_schema": t.get("parameters", {"type": "object", "properties": {}}),
        }
        for t in tools
    ]


class AnthropicAdapter(ToolCallAdapter):
    """Anthropic Claude adapter for TeamBench.

    Uses the anthropic >= 0.20 SDK with the Messages API and tool use.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.2,
        max_tokens: int = 8192,
    ):
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "The 'anthropic' package is required for AnthropicAdapter. "
                "Install it with: pip install anthropic"
            ) from exc

        self.model = model
        self.temperature = temperature
        # Some models reject `temperature` outright:
        #   400 invalid_request_error: `temperature` is deprecated for this model
        # Rather than keep a list of which models accept it, which goes stale on
        # every release, the first such rejection sets this flag and the request
        # is retried without the field. Every later call omits it too.
        self._omit_temperature = False
        self.max_tokens = max_tokens
        self._total_input_tokens = 0
        self._total_output_tokens = 0

        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            key = _load_key_from_dotenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. Provide api_key or set the environment variable."
            )
        self._client = anthropic.Anthropic(api_key=key, timeout=120.0)

    # ------------------------------------------------------------------
    # ToolCallAdapter interface
    # ------------------------------------------------------------------

    def generate_with_tools(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: list[dict],
    ) -> AdapterResponse:
        """Call Anthropic Messages API with tools and return AdapterResponse."""
        anthropic_messages = self._build_messages(messages)
        anthropic_tools = _standard_to_anthropic_tools(tools) if tools else []

        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": anthropic_messages,
        }
        if not self._omit_temperature:
            kwargs["temperature"] = self.temperature
        if system_prompt:
            kwargs["system"] = system_prompt
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        response = self._call_with_retry(**kwargs)
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

    def generate(
        self,
        messages: list[dict],
        system_prompt: str,
    ) -> AdapterResponse:
        """Call Anthropic Messages API without tools and return AdapterResponse."""
        anthropic_messages = self._build_messages(messages)

        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": anthropic_messages,
        }
        if not self._omit_temperature:
            kwargs["temperature"] = self.temperature
        if system_prompt:
            kwargs["system"] = system_prompt

        response = self._call_with_retry(**kwargs)
        self._track_usage(response)
        return self._parse_response(response)

    def _call_with_retry(self, max_retries: int = 5, **kwargs) -> Any:
        """Call Anthropic API with exponential backoff retry on transient errors."""
        import anthropic

        for attempt in range(max_retries):
            try:
                return self._client.messages.create(**kwargs)
            except (
                anthropic.RateLimitError,
                anthropic.InternalServerError,
                anthropic.APIConnectionError,
                anthropic.APITimeoutError,
            ) as exc:
                if attempt == max_retries - 1:
                    raise
                wait = min(2 ** attempt * 5, 120)
                logger.warning(
                    "Anthropic API error (attempt %d/%d): %s — retrying in %ds",
                    attempt + 1, max_retries, exc, wait,
                )
                time.sleep(wait)
            except anthropic.BadRequestError as exc:
                # Placed AFTER the transient-error handlers so it cannot shadow
                # them. A 400 is not transient, so the backoff loop above would
                # otherwise retry the identical request until it gave up.
                #
                # The one 400 worth recovering from: `temperature` is deprecated
                # for this model. Drop the field, retry, and remember for the
                # rest of the run. Keeping a list of which models still accept
                # temperature would go stale on every release.
                if ("temperature" in str(exc) and "deprecated" in str(exc)
                        and "temperature" in kwargs):
                    self._omit_temperature = True
                    kwargs.pop("temperature", None)
                    logger.warning("model rejects `temperature`; retrying without it")
                    continue
                raise
        raise RuntimeError("Unreachable")

    def _build_messages(self, messages: list[dict]) -> list[dict]:
        """Convert standard message dicts to Anthropic messages format.

        Anthropic requires alternating user/assistant turns and the
        conversation must end with a user message (no assistant prefill).
        "tool" role (tool results already formatted as text) map to "user".
        """
        anthropic_msgs: list[dict] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "tool"):
                mapped_role = "user"
            elif role == "assistant":
                mapped_role = "assistant"
            else:
                mapped_role = "user"

            # Merge consecutive same-role messages
            if anthropic_msgs and anthropic_msgs[-1]["role"] == mapped_role:
                anthropic_msgs[-1]["content"] += "\n\n" + content
            else:
                anthropic_msgs.append({"role": mapped_role, "content": content})

        # Ensure conversation ends with a user message (required by some models)
        if anthropic_msgs and anthropic_msgs[-1]["role"] == "assistant":
            anthropic_msgs.append({"role": "user", "content": "Continue."})

        return anthropic_msgs

    def _parse_response(self, response: Any) -> AdapterResponse:
        """Parse an Anthropic Message into AdapterResponse."""
        text = ""
        tool_calls: list[dict] = []

        for block in response.content or []:
            block_type = getattr(block, "type", "")
            if block_type == "text":
                text += block.text or ""
            elif block_type == "tool_use":
                tool_calls.append({
                    "name": block.name,
                    "args": block.input or {},
                })

        done = "DONE" in text or "TASK_COMPLETE" in text
        return AdapterResponse(text=text, tool_calls=tool_calls, done=done)

    def _track_usage(self, response: Any) -> None:
        """Accumulate token counts from response usage."""
        usage = getattr(response, "usage", None)
        if usage:
            self._total_input_tokens += getattr(usage, "input_tokens", 0) or 0
            self._total_output_tokens += getattr(usage, "output_tokens", 0) or 0
