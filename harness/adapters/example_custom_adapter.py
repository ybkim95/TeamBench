"""
Example custom adapter for TeamBench.

Copy this file to `harness/adapters/<your_provider>_adapter.py`, fill in the
two abstract methods, then register a model-name prefix in
`harness/adapters/__init__.py` so `--model <prefix>:<name>` routes here.

Minimum dependencies: just whatever Python client your provider needs.
TeamBench itself only depends on `harness.agent_interface`.

To smoke-test once wired up:

    python -m harness.ablation --model custom:<name> --tasks DIST1_queue_race \\
        --seeds 0 --conditions oracle --output /tmp/teambench_custom

See `harness/adapters/openai_adapter.py` for a production reference and
`harness/adapters/mock_adapter.py` for the simplest possible implementation.
"""
from __future__ import annotations

import os
from typing import Any

from harness.agent_interface import AdapterResponse, ToolCallAdapter


class ExampleCustomAdapter(ToolCallAdapter):
    """Replace this docstring + class name with your provider.

    The agent loop calls `generate_with_tools(...)` each turn and expects a
    well-formed AdapterResponse back. Three fields matter:
      - text:       free-form assistant text the agent shows in messages
      - tool_calls: list of {"name": str, "args": dict} the agent will execute
      - done:       True if the model signaled task completion (rare; the loop
                    usually ends when the agent calls the `attest` tool, so
                    most adapters can leave this False).
    """

    def __init__(self, model: str, temperature: float = 0.2, **kwargs: Any) -> None:
        self.model = model
        self.temperature = temperature
        # Pull any API keys / base URLs you need:
        # self.api_key = os.environ.get("YOUR_PROVIDER_API_KEY") or kwargs.get("api_key")
        # Initialise the underlying client here.
        self._prompt_tokens = 0
        self._completion_tokens = 0

    def generate_with_tools(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: list[dict],
    ) -> AdapterResponse:
        """Single-turn completion with tool calling.

        Args:
            messages: chat history. Each item is `{"role": ..., "content": ...}`
                with role in {"user", "assistant", "tool"}. Tool results show up
                as role="tool" with content being the tool output string.
            system_prompt: role-specific system prompt assembled by TeamBench
                (Planner / Executor / Verifier system prompts differ; the
                adapter does not need to know which role).
            tools: tool declarations in the standard JSON-Schema-style format
                produced by `harness.agent_interface.tools_to_standard_declarations`.
                Each item has `name`, `description`, `parameters` (JSON Schema).

        Returns:
            AdapterResponse with `text` and `tool_calls`. Tool calls must list
            `name` and `args`; the agent loop dispatches them by name.
        """
        # === 1. Translate `tools` into your provider's native tool format. ===
        # Most chat APIs (OpenAI, Anthropic, Gemini) accept JSON-Schema tool
        # declarations directly with minor field renames.
        # provider_tools = [...]

        # === 2. Translate `messages` into your provider's chat format. ===
        # Pay attention to how the provider expects tool-result messages.
        # provider_messages = [...]

        # === 3. Call the provider. ===
        # response = self._client.generate(
        #     model=self.model,
        #     system=system_prompt,
        #     messages=provider_messages,
        #     tools=provider_tools,
        #     temperature=self.temperature,
        # )
        # self._prompt_tokens     += response.usage.input_tokens
        # self._completion_tokens += response.usage.output_tokens

        # === 4. Extract text and tool calls from the response. ===
        text = ""           # final assistant message content
        tool_calls: list[dict] = []
        # Each tool call must be: {"name": "<tool_name>", "args": {<json_args>}}
        # for tc in response.tool_calls:
        #     tool_calls.append({"name": tc.name, "args": tc.parsed_args})

        return AdapterResponse(text=text, tool_calls=tool_calls, done=False)

    def get_usage(self) -> dict:
        """Return cumulative token usage for telemetry."""
        return {
            "input_tokens": self._prompt_tokens,
            "output_tokens": self._completion_tokens,
            "total_tokens": self._prompt_tokens + self._completion_tokens,
        }


# To wire this adapter in, edit `harness/adapters/__init__.py` and add a
# branch in `create_adapter`, for example:
#
#     if model_lower.startswith("custom:"):
#         from harness.adapters.example_custom_adapter import ExampleCustomAdapter
#         return ExampleCustomAdapter(model=model[len("custom:"):], temperature=temperature, **kwargs)
#
# Then run:
#     python -m harness.ablation --model custom:my-model-name --tasks DIST1_queue_race \
#         --seeds 0 --conditions oracle --output /tmp/teambench_custom
