"""
Observability providers for redis-py.
"""
from typing import Optional


class ObservabilityInstance:
    """Represents an observability instance for Redis."""

    def __init__(self):
        pass


_observability_instance: Optional[ObservabilityInstance] = None


def get_observability_instance() -> Optional[ObservabilityInstance]:
    """Get the current observability instance."""
    global _observability_instance
    return _observability_instance


def reset_observability_instance() -> None:
    """Reset the current observability instance."""
    global _observability_instance
    _observability_instance = None
