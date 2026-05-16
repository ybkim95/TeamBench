"""
Simplified pytest-like test framework.

Supports function, module, and session fixture scopes. Session-scoped fixtures
are cached for the duration of the test run so the factory is only invoked once.
"""

from __future__ import annotations

import copy
import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class Fixture:
    """Metadata for a registered fixture."""

    def __init__(self, name: str, func: Callable, scope: str = "function") -> None:
        self.name = name
        self.func = func
        self.scope = scope  # "function" | "module" | "session"

    def __repr__(self) -> str:
        return f"Fixture(name={self.name!r}, scope={self.scope!r})"


# ---------------------------------------------------------------------------
# Fixture manager
# ---------------------------------------------------------------------------

class FixtureManager:
    """Manages fixture registration, caching, and retrieval."""

    def __init__(self) -> None:
        self._registry: Dict[str, Fixture] = {}
        # Cache keyed by scope name, then fixture name.
        # "function"  -> {scope_key: value}
        # "module"    -> {name: value}
        # "session"   -> {name: value}
        self._cache: Dict[str, Dict[str, Any]] = {
            "function": {},
            "module": {},
            "session": {},
        }

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, name: str, func: Callable, scope: str = "function") -> None:
        """Register a fixture factory under *name* with the given *scope*."""
        if scope not in ("function", "module", "session"):
            raise ValueError(f"Unknown scope {scope!r}; expected function/module/session")
        self._registry[name] = Fixture(name=name, func=func, scope=scope)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_fixture(self, name: str, scope_key: str = "") -> Any:
        """Return the value for fixture *name*.

        - function scope: always calls the factory (fresh per test).
        - module scope:   caches per module (cache cleared between modules).
        - session scope:  caches for the entire session (factory called once).
        """
        if name not in self._registry:
            raise KeyError(f"No fixture registered with name {name!r}")

        fixture = self._registry[name]

        if fixture.scope == "function":
            # Always fresh — no caching.
            return fixture.func()

        if fixture.scope == "module":
            if name not in self._cache["module"]:
                self._cache["module"][name] = fixture.func()
            return self._cache["module"][name]

        # scope == "session"
        if name not in self._cache["session"]:
            self._cache["session"][name] = fixture.func()
        # BUG: returns the cached object reference directly.
        # Any caller that mutates the returned value will corrupt the cache
        # for all subsequent requestors in the same session.
        return copy.deepcopy(self._cache["session"][name])

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def clear_scope(self, scope: str) -> None:
        """Clear all cached values for *scope*."""
        if scope not in self._cache:
            raise ValueError(f"Unknown scope {scope!r}")
        self._cache[scope].clear()


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

class TestRunner:
    """Discovers and runs test functions, injecting fixtures by parameter name."""

    def __init__(self, fixture_manager: FixtureManager) -> None:
        self._fm = fixture_manager

    def discover(self, module: Dict[str, Any]) -> List[str]:
        """Return names of test functions (test_*) found in *module* dict."""
        return [name for name, obj in module.items()
                if name.startswith("test_") and callable(obj)]

    def run_module(
        self,
        module_name: str,
        tests: Dict[str, Callable],
        fixtures: Optional[List[str]] = None,
    ) -> List[Tuple[str, bool, Optional[str]]]:
        """Run all tests in *tests*, injecting fixtures by parameter name.

        Args:
            module_name: Identifier used as the scope_key for module-level fixtures.
            tests:       Mapping of test-function-name -> callable.
            fixtures:    Explicit list of fixture names to inject (optional).
                         When None, parameter names are inferred via inspect.

        Returns:
            List of (test_name, passed, error_message_or_None).
        """
        results: List[Tuple[str, bool, Optional[str]]] = []

        for test_name, test_fn in tests.items():
            # Resolve which fixtures this test needs.
            if fixtures is not None:
                needed = fixtures
            else:
                sig = inspect.signature(test_fn)
                needed = list(sig.parameters.keys())

            kwargs: Dict[str, Any] = {}
            try:
                for fix_name in needed:
                    kwargs[fix_name] = self._fm.get_fixture(fix_name, scope_key=module_name)
                test_fn(**kwargs)
                results.append((test_name, True, None))
            except AssertionError as exc:
                results.append((test_name, False, str(exc)))
            except Exception as exc:  # noqa: BLE001
                results.append((test_name, False, f"{type(exc).__name__}: {exc}"))

            # Clear function-scoped cache after each test.
            self._fm.clear_scope("function")

        # Clear module-scoped cache after the module finishes.
        self._fm.clear_scope("module")

        return results

    def run_all(
        self,
        modules: List[Tuple[str, Dict[str, Callable]]],
    ) -> Dict[str, List[Tuple[str, bool, Optional[str]]]]:
        """Run all *modules* sequentially.

        Args:
            modules: List of (module_name, {test_name: callable}) pairs.

        Returns:
            Dict mapping module_name -> run_module() results.
        """
        all_results: Dict[str, List[Tuple[str, bool, Optional[str]]]] = {}
        for module_name, tests in modules:
            all_results[module_name] = self.run_module(module_name, tests)
        return all_results


# ---------------------------------------------------------------------------
# Decorator API
# ---------------------------------------------------------------------------

_global_manager = FixtureManager()


def fixture(scope: str = "function") -> Callable:
    """Decorator that registers a function as a fixture with the global manager."""
    def decorator(func: Callable) -> Callable:
        _global_manager.register(func.__name__, func, scope=scope)
        return func
    return decorator


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_tests(
    modules: List[Tuple[str, Dict[str, Callable]]],
    manager: Optional[FixtureManager] = None,
) -> Dict[str, List[Tuple[str, bool, Optional[str]]]]:
    """Run all test modules and return results.

    Uses *manager* if provided, otherwise the global fixture manager.
    """
    mgr = manager if manager is not None else _global_manager
    runner = TestRunner(mgr)
    return runner.run_all(modules)
