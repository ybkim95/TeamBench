import os
import json


class ConfigValidationError(ValueError):
    """Raised when a config value fails validation."""
    pass


_SCHEMA = {
    "queue_url": {
        "type": "string",
        "default": "redis://localhost:6379/0",
        "env_var": "CELERY_QUEUE_URL",
    },
    "concurrency": {
        "type": "int",
        "default": 3,
        "env_var": "CELERY_CONCURRENCY",
        "min": 1,
        "max": 32,
    },
    "max_retries": {
        "type": "int",
        "default": 8,
        "env_var": "CELERY_MAX_RETRIES",
        "min": 0,
        "max": 20,
    },
    "retry_backoff_seconds": {
        "type": "int",
        "default": 1,
        "env_var": "CELERY_RETRY_BACKOFF",
        "min": 1,
        "max": 300,
    },
    "job_timeout": {
        "type": "int",
        "default": 300,
        "env_var": "CELERY_JOB_TIMEOUT",
        "min": 1,
        "max": 3600,
    },
    "log_level": {
        "type": "enum",
        "default": "INFO",
        "env_var": "CELERY_LOG_LEVEL",
        "allowed": ["DEBUG", "INFO", "WARN"],
    },
    "dead_letter_queue": {
        "type": "bool",
        "default": True,
        "env_var": "CELERY_DEAD_LETTER",
    },
    "heartbeat_interval": {
        "type": "int",
        "default": 60,
        "env_var": "CELERY_HEARTBEAT",
        "min": 5,
        "max": 300,
    },
    "prefetch_count": {
        "type": "int",
        "default": 10,
        "env_var": "CELERY_PREFETCH",
        "min": 1,
        "max": 100,
    },
    "ack_on_failure": {
        "type": "bool",
        "default": False,
        "env_var": "CELERY_ACK_ON_FAILURE",
    },
    "metrics_enabled": {
        "type": "bool",
        "default": True,
        "env_var": "CELERY_METRICS",
    },
}

_BOOL_TRUE = {"true", "1", "yes", "on"}
_BOOL_FALSE = {"false", "0", "no", "off"}


def get_schema() -> dict:
    """Return the config schema as a dict (key -> spec dict)."""
    return _SCHEMA


def validate_value(key: str, value) -> object:
    """
    Validate and coerce a single value against the schema for `key`.
    Returns the coerced value. Raises ConfigValidationError if invalid.
    """
    if key not in _SCHEMA:
        raise ConfigValidationError(f"Unknown config key: {key!r}")

    spec = _SCHEMA[key]
    vtype = spec["type"]

    if vtype == "string":
        if not isinstance(value, str):
            value = str(value)
        if value == "":
            raise ConfigValidationError(
                f"Invalid value for '{key}': must be a non-empty string"
            )
        return value

    elif vtype == "int":
        # bool is subclass of int in Python — check bool first
        if isinstance(value, bool):
            raise ConfigValidationError(
                f"Invalid value for '{key}': {value!r} is not a valid integer"
            )
        if isinstance(value, int):
            int_val = value
        elif isinstance(value, str):
            try:
                int_val = int(value)
            except ValueError:
                raise ConfigValidationError(
                    f"Invalid value for '{key}': {value!r} is not a valid integer"
                )
        else:
            try:
                int_val = int(value)
            except (ValueError, TypeError):
                raise ConfigValidationError(
                    f"Invalid value for '{key}': {value!r} is not a valid integer"
                )
        min_val = spec.get("min")
        max_val = spec.get("max")
        if min_val is not None and int_val < min_val:
            raise ConfigValidationError(
                f"Invalid value for '{key}': {int_val} is out of range [{min_val}, {max_val}]"
            )
        if max_val is not None and int_val > max_val:
            raise ConfigValidationError(
                f"Invalid value for '{key}': {int_val} is out of range [{min_val}, {max_val}]"
            )
        return int_val

    elif vtype == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            if value == 1:
                return True
            elif value == 0:
                return False
            else:
                raise ConfigValidationError(
                    f"Invalid value for '{key}': {value!r} is not a valid boolean"
                )
        if isinstance(value, str):
            lower = value.lower()
            if lower in _BOOL_TRUE:
                return True
            elif lower in _BOOL_FALSE:
                return False
            else:
                raise ConfigValidationError(
                    f"Invalid value for '{key}': {value!r} is not a valid boolean; "
                    f"accepted values: true/false, 1/0, yes/no, on/off"
                )
        raise ConfigValidationError(
            f"Invalid value for '{key}': {value!r} is not a valid boolean"
        )

    elif vtype == "enum":
        if not isinstance(value, str):
            value = str(value)
        allowed = spec["allowed"]
        if value not in allowed:
            raise ConfigValidationError(
                f"Invalid value for '{key}': {value!r} is not one of {allowed}"
            )
        return value

    else:
        raise ConfigValidationError(f"Unknown type {vtype!r} for key '{key}'")


def load_config(
    config_file=None,
    env_vars=None,
    cli_args=None,
) -> dict:
    """
    Load and validate configuration from all sources in priority order.
    Priority (highest first): cli_args > env_vars > config_file > defaults
    """
    if env_vars is None:
        env_vars = os.environ

    # Start with defaults
    result = {key: spec["default"] for key, spec in _SCHEMA.items()}

    # Layer 2: config file (lowest priority after defaults)
    if config_file is not None:
        # Let FileNotFoundError propagate naturally from open()
        with open(config_file, "r") as f:
            file_data = json.load(f)
        for key in _SCHEMA:
            if key in file_data:
                result[key] = file_data[key]

    # Layer 3: environment variables
    for key, spec in _SCHEMA.items():
        env_key = spec["env_var"]
        if env_key in env_vars:
            result[key] = env_vars[env_key]

    # Layer 4 (highest): CLI args
    if cli_args is not None:
        for key in _SCHEMA:
            if key in cli_args and cli_args[key] is not None:
                result[key] = cli_args[key]

    # Validate and coerce all values
    final = {}
    for key in _SCHEMA:
        final[key] = validate_value(key, result[key])

    return final
