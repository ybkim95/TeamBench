# Specification: GH7 Fixture Scope Leak

## Issue

`@fixture(scope="session")` returning a mutable object (e.g., `[]` or `{}`) leaks
mutations between test modules. Module A appends to the list; Module B sees the
appended items. This mirrors a real pytest fixture isolation issue.

## Root Cause

In `FixtureManager.get_fixture(name, scope_key)`, session-scoped fixtures are cached
by fixture name only. When the fixture factory returns a mutable object, the **same
object reference** is returned to every requestor across all modules. The cache stores
`{name: value}` but should either:

1. Store the factory and re-invoke it per module-scope request, OR
2. Return `copy.deepcopy(cached_value)` for each call while keeping the canonical
   copy in the cache.

Option 2 (deep-copy on return) is the minimal fix because it requires changing only
the return path inside `get_fixture()`.

## The Fix

In `get_fixture()`, after retrieving a cached session-scoped value, return a deep copy
of that value rather than the cached reference directly:

```python
import copy
# inside get_fixture, when serving a cached session fixture:
return copy.deepcopy(self._cache["session"][name])
```

The canonical cached value is never mutated by callers, so subsequent calls always
deep-copy from the original.

## Constraints

- **Function-scoped fixtures already work correctly** (re-invoked per test via
  `clear_scope("function")`). Do not change this behavior.
- **Module-scoped fixtures already work correctly** (cleared between modules via
  `clear_scope("module")`). Do not change this behavior.
- **Session-scoped fixtures with immutable values** (strings, ints, tuples) must
  still be cached efficiently. `copy.deepcopy` is safe and correct for these types;
  it returns equal values and the factory is still called only once.
- **The test discovery and test runner logic are correct** and must not be changed.
- **`FixtureManager` class must remain present** with its public interface intact.

## Affected Files

Only `test_framework.py` needs to be modified. The change is approximately 1–3 lines
inside `FixtureManager.get_fixture()`.
