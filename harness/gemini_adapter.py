"""
Gemini adapter for TeamBench agent driver.

Uses the google-genai SDK (GA package) with manual function calling.
"""
from __future__ import annotations

import os
import time
from typing import Any, Optional

from google import genai
from google.genai import types

from harness.agent_interface import ModelAdapter, Tool


def tools_to_gemini_declarations(tools: list[Tool]) -> list[types.Tool]:
    """Convert TeamBench Tool objects to Gemini FunctionDeclaration schemas."""
    declarations = []
    for tool in tools:
        if tool.name == "run":
            declarations.append(types.FunctionDeclaration(
                name="run",
                description="Execute a shell command in the workspace. Returns stdout, stderr, and exit code.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "cmd": types.Schema(type="STRING", description="Shell command to execute"),
                    },
                    required=["cmd"],
                ),
            ))
        elif tool.name == "read":
            declarations.append(types.FunctionDeclaration(
                name="read",
                description="Read the contents of a file. Path must be within allowed directories.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "path": types.Schema(type="STRING", description="Path to the file to read"),
                    },
                    required=["path"],
                ),
            ))
        elif tool.name == "write":
            declarations.append(types.FunctionDeclaration(
                name="write",
                description="Write content to a file. Path must be within allowed directories.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "path": types.Schema(type="STRING", description="Path to the file to write"),
                        "content": types.Schema(type="STRING", description="Content to write to the file"),
                    },
                    required=["path", "content"],
                ),
            ))
        elif tool.name == "send_message":
            declarations.append(types.FunctionDeclaration(
                name="send_message",
                description="Send a message to another agent role (planner, executor, or verifier).",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "to": types.Schema(type="STRING", description="Target role: planner, executor, or verifier"),
                        "content": types.Schema(type="STRING", description="Message content"),
                    },
                    required=["to", "content"],
                ),
            ))
    return [types.Tool(function_declarations=declarations)]


class GeminiAdapter(ModelAdapter):
    """Gemini model adapter with tool calling support."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.2,
        max_output_tokens: int = 8192,
    ):
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self._total_input_tokens = 0
        self._total_output_tokens = 0

        key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not key:
            raise ValueError("GEMINI_API_KEY not set. Provide api_key or set the environment variable.")
        self.client = genai.Client(api_key=key)

    def generate(self, messages: list[dict], **kwargs) -> str:
        """Simple text generation (ModelAdapter contract)."""
        contents = []
        system_instruction = None
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            elif msg["role"] == "user":
                contents.append(types.Content(role="user", parts=[types.Part.from_text(text=msg["content"])]))
            elif msg["role"] == "assistant":
                contents.append(types.Content(role="model", parts=[types.Part.from_text(text=msg["content"])]))

        response = self._call_with_retry(
            contents=contents,
            system_instruction=system_instruction,
        )
        self._track_usage(response)
        return response.text or ""

    def generate_with_tools(
        self,
        contents: list[types.Content],
        system_instruction: str | None = None,
        tools: list[types.Tool] | None = None,
    ) -> types.GenerateContentResponse:
        """Generate with function calling support. Returns raw response for tool processing."""
        response = self._call_with_retry(
            contents=contents,
            system_instruction=system_instruction,
            tools=tools,
        )
        self._track_usage(response)
        return response

    def _call_with_retry(
        self,
        contents: list[types.Content],
        system_instruction: str | None = None,
        tools: list[types.Tool] | None = None,
        max_retries: int = 5,
    ) -> types.GenerateContentResponse:
        """Call Gemini API with exponential backoff for rate limits."""
        config = types.GenerateContentConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            tools=tools,
        )
        if system_instruction:
            config.system_instruction = system_instruction

        for attempt in range(max_retries):
            try:
                return self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=config,
                )
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "resource_exhausted" in error_str or "rate" in error_str:
                    wait = min(2 ** attempt * 2, 60)
                    print(f"  [rate-limit] Retry {attempt + 1}/{max_retries} in {wait}s...")
                    time.sleep(wait)
                    continue
                raise
        raise RuntimeError(f"Gemini API failed after {max_retries} retries")

    def _track_usage(self, response: types.GenerateContentResponse) -> None:
        """Track token usage from response metadata."""
        meta = getattr(response, "usage_metadata", None)
        if meta:
            self._total_input_tokens += getattr(meta, "prompt_token_count", 0) or 0
            self._total_output_tokens += getattr(meta, "candidates_token_count", 0) or 0

    def get_usage(self) -> dict:
        """Return cumulative token usage."""
        return {
            "input_tokens": self._total_input_tokens,
            "output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "model": self.model,
        }
