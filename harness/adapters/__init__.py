"""
TeamBench provider adapters.

Each adapter implements ToolCallAdapter from harness.agent_interface.
Import the adapter you need; only that provider's SDK is required.

Available adapters:
  - GeminiAdapter   (harness.gemini_adapter)          requires: google-genai
  - OpenAIAdapter   (harness.adapters.openai_adapter) requires: openai
  - AnthropicAdapter(harness.adapters.anthropic_adapter) requires: anthropic
"""
from __future__ import annotations


def create_adapter(model: str, temperature: float = 0.2, **kwargs):
    """Factory: instantiate the correct adapter based on model name prefix.

    Supported prefixes:
      gemini-*   -> GeminiAdapter  (GEMINI_API_KEY)
      gpt-* / o* -> OpenAIAdapter  (OPENAI_API_KEY)
      claude-*   -> AnthropicAdapter (ANTHROPIC_API_KEY)
    """
    model_lower = model.lower()

    if model_lower.startswith("gemini"):
        from harness.gemini_adapter import GeminiAdapter
        return GeminiAdapter(model=model, temperature=temperature, **kwargs)

    if model_lower.startswith(("gpt-", "o1", "o3", "o4")):
        from harness.adapters.openai_adapter import OpenAIAdapter
        return OpenAIAdapter(model=model, temperature=temperature, **kwargs)

    if model_lower.startswith("claude"):
        from harness.adapters.anthropic_adapter import AnthropicAdapter
        return AnthropicAdapter(model=model, temperature=temperature, **kwargs)

    if model_lower.startswith("mock"):
        from harness.adapters.mock_adapter import MockAdapter
        return MockAdapter(temperature=temperature, **kwargs)

    raise ValueError(
        f"Cannot determine adapter for model '{model}'. "
        "Use a model name starting with 'gemini-', 'gpt-', 'o1', 'o3', 'o4', 'claude-', or 'mock'."
    )
