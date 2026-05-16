"""
Observability package for redis-py.

Re-exports the public API symbols for convenient access via `from redis.observability import ...`.
"""

from redis.observability.config import MetricGroup, OTelConfig, TelemetryOption
from redis.observability.providers import (
    ObservabilityInstance,
    get_observability_instance,
    reset_observability_instance,
)

__all__ = [
    "OTelConfig",
    "MetricGroup",
    "TelemetryOption",
    "ObservabilityInstance",
    "get_observability_instance",
    "reset_observability_instance",
]
