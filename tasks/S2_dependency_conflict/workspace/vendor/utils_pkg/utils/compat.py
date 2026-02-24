"""Compatibility layer -- routes to the appropriate implementation."""
try:
    from utils.legacy import helper
except ImportError:
    from utils.v2 import helper

__all__ = ["helper"]
