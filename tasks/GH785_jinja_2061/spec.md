# GH785_jinja_2061: fix default for `Environment.overlay(enable_async)` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pallets/jinja

## PR Description

Got a wrong behaviour with `Environment.overlay` and seems to me an obvious error code.

## PR Review Comments

**[user]** on `tests/test_api.py`:

Missing test case of the concerning issue with `overlay` without any `enable_async` parameter , that is : 
```python
    assert env_async.overlay().is_async
 ```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
