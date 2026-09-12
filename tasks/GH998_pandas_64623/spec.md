# GH998_pandas_64623: TST: add regression test for #26558 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pandas-dev/pandas

## PR Description

## Summary

Adds a regression test for `DataFrame.add(fill_value=0)` when the index is a `MultiIndex` containing a mix of string and `datetime` labels.

References: #26558 

## Why

I couldn’t reproduce the incorrect result from GH#26558 on current `main`, but I also couldn’t find a test covering this exact case. This adds coverage for the behavior so we don’t regress it later.

## Testing

- Added a targeted test in `pandas/tests/frame/test_arithmetic.py`
- Ran:
  ```bash
  python -m pytest pandas/tests/frame/test_arithmetic.py -k mixed_string_datetime_index -n 0
  ```
- Result: passed

## PR Review Comments

**[user]** on `pandas/tests/frame/test_arithmetic.py`:

Whenever possible, test the full state of the result.

```python
expected = DataFrame(...)
tm.assert_frame_equal(result, expected)
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
