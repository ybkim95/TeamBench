# GH112_redis-py_3996: Expose basic Otel classes and funtions to be importable through redis.observability to match the examples in the readthedocs — Full Specification (Planner Only)

## Source
- PR: https://github.com/redis/redis-py/pull/3996
- Issue: https://github.com/redis/redis-py/issues/3992
- Repo: https://github.com/redis/redis-py

## Issue Description

Documentation example imports should be adjusted.
https://redis.readthedocs.io/en/stable/opentelemetry.html

from:
```
# 2. Initialize redis-py observability
from redis.observability import get_observability_instance, OTelConfig
```

to:
```
# 2. Initialize redis-py observability
from redis.observability.config import OTelConfig
from redis.observability.providers import get_observability_instance
```

```
[[package]]
name = "redis"
version = "7.3.0"
```

or add these exports to the `__init__.py` file..

## Issue Discussion (Root Cause Analysis)

### Comment 1 (@petyaslavova):

Hey @vpmedia, thanks for bringing this to our attention. We will provide a fix for this soon.

## PR Review Comments

**@Copilot** on `redis/observability/__init__.py`:

This new public import surface (`from redis.observability import ...`) isn’t currently covered by tests. Since the goal is to keep docs/examples working, add a small unit test that imports the re-exported symbols from `redis.observability` (e.g., `OTelConfig`, `MetricGroup`, `get_observability_instance`, `reset_observability_instance`) and asserts they are the same objects as the originals, to prevent regressions.

**@petyaslavova** on `redis/observability/__init__.py`:

done.

## Files Changed in Fix

- `redis/observability/__init__.py` (modified, +27/-0)
- `tests/test_observability/test_public_api.py` (added, +83/-0)

## `redis/observability/__init__.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify the source files listed above (not test files)
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
