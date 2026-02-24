"""
Task generator registry.

Maps task_id to generator class. Generators are auto-discovered from the
generators/ directory by naming convention: gen_{task_id}.py must define
a class named Generator that subclasses TaskGenerator.
"""
from __future__ import annotations

import importlib
import os
from typing import Optional

from generators.base import TaskGenerator

# Manual registry for explicit control
_REGISTRY: dict[str, type[TaskGenerator]] = {}


def register(task_id: str, generator_cls: type[TaskGenerator]) -> None:
    """Register a generator class for a task_id."""
    _REGISTRY[task_id] = generator_cls


def get_generator(task_id: str) -> TaskGenerator:
    """
    Get an instantiated generator for a task_id.

    Tries manual registry first, then auto-discovery from generators/gen_{task_id}.py.
    """
    if task_id in _REGISTRY:
        return _REGISTRY[task_id]()

    # Auto-discovery
    module_name = f"generators.gen_{task_id.lower()}"
    try:
        mod = importlib.import_module(module_name)
        cls = getattr(mod, "Generator")
        _REGISTRY[task_id] = cls
        return cls()
    except (ImportError, AttributeError):
        pass

    raise KeyError(
        f"No generator found for task_id={task_id}. "
        f"Create generators/gen_{task_id.lower()}.py with a Generator class, "
        f"or register one via generators.registry.register()."
    )


def has_generator(task_id: str) -> bool:
    """Check if a parameterized generator exists for this task."""
    if task_id in _REGISTRY:
        return True
    module_name = f"generators.gen_{task_id.lower()}"
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def list_generators() -> list[str]:
    """List all available generator task_ids (both registered and auto-discoverable)."""
    gen_dir = os.path.dirname(os.path.abspath(__file__))
    task_ids = set(_REGISTRY.keys())
    for fname in os.listdir(gen_dir):
        if fname.startswith("gen_") and fname.endswith(".py"):
            tid = fname[4:-3]  # strip gen_ prefix and .py suffix
            # Convert back to original case by checking tasks/ directory
            task_ids.add(tid)
    return sorted(task_ids)
