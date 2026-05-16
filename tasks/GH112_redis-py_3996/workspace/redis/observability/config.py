"""
Observability configuration for redis-py.
"""
from enum import Enum


class TelemetryOption(Enum):
    """Options for telemetry configuration."""
    ENABLED = "enabled"
    DISABLED = "disabled"


class MetricGroup(Enum):
    """Groups of metrics that can be collected."""
    COMMANDS = "commands"
    CONNECTIONS = "connections"
    POOLS = "pools"


class OTelConfig:
    """Configuration for OpenTelemetry observability."""

    def __init__(
        self,
        telemetry_option: TelemetryOption = TelemetryOption.ENABLED,
        metric_groups: list = None,
    ):
        self.telemetry_option = telemetry_option
        self.metric_groups = metric_groups or list(MetricGroup)
