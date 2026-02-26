"""
New feature implementation: strict_mode

Add strict validation that raises on any anomaly to TextParser WITHOUT breaking any existing behavior.

Instructions:
  1. Implement the `enable_strict_mode` function below.
  2. Monkey-patch or subclass TextParser if needed, but do NOT modify core.py.
  3. All existing tests in tests/test_legacy.py must continue to pass.
  4. The new tests in tests/test_new_feature.py must also pass.
"""
from textparser import TextParser


def enable_strict_mode(instance):
    """
    Add strict validation that raises on any anomaly capability to an existing TextParser instance.

    Args:
        instance: An existing TextParser instance to enhance.

    Returns:
        The enhanced instance (same object, augmented in-place).

    TODO: Implement this function.
    """
    raise NotImplementedError("enable_strict_mode is not yet implemented")
