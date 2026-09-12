# GH479_redis-py_3972: Fix race condition in RESP3 parser buffer purge — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/redis/redis-py

## PR Description

`self._buffer` can be set to `None` by another thread between the None check and the `purge()` call, causing an unhandled `AttributeError` in the `else` branch of `read_response`.

## Changes

- **`redis/_parsers/resp3.py`**: Combine the `self._buffer is not None` guard with a `try/except AttributeError` to handle the TOCTOU race condition — consistent with the existing pattern on lines 32 and 38:

```python
# Before
try:
    self._buffer.purge()
except AttributeError:
    pass

# After
if self._buffer is not None:
    try:
        self._buffer.purge()
    except AttributeError:
        # Buffer may have been set to None by another thread after
        # the check above; result is still valid so we don't raise
        pass
```

<!-- START COPILOT CODING AGENT TIPS -->
---

💬 We'd love your input! Share your thoughts on Copilot coding agent in our [2 minute survey](https://gh.io/copilot-coding-agent-survey).

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
