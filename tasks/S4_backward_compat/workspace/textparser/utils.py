"""
Internal utility functions.
These are private and may change between versions.
"""


def normalize_string(s: str) -> str:
    """Normalize whitespace in a string."""
    return " ".join(s.split())


def flatten_dict(d: dict, prefix: str = "") -> dict:
    """Flatten a nested dict to dot-separated keys."""
    result = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            result.update(flatten_dict(v, key))
        else:
            result[key] = v
    return result


def safe_cast(value, target_type, default=None):
    """Safely cast a value to target_type, returning default on failure."""
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return default
