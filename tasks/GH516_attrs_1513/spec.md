# GH516_attrs_1513: Fix validators.disabled() to save/restore state on nesting — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/python-attrs/attrs

## PR Description

## Summary

`validators.disabled()` unconditionally re-enables validators in its `finally` block instead of restoring the previous state. This breaks nested usage — the inner context manager prematurely re-enables validators when it exits.

```python
with disabled():
    with disabled():
        pass
    # BUG: validators are now ENABLED even though we're still in the outer disabled()
    C(x="not_int")  # raises TypeError unexpectedly
```

The fix saves the current state with `get_run_validators()` before disabling, then restores it in `finally`. This is a one-line semantic change.

The same pattern of nesting breakage also applies when `set_run_validators(False)` was called before entering `disabled()` — the context manager would unexpectedly override that.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
