# GH923_pandas_64643: BUG: fix float-to-int64 OOB handling on ARM in to_datetime/to_timedelta — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pandas-dev/pandas

## PR Description

## Summary

Follow-up to #64619. On ARM, float-to-int64 overflow saturates to `INT64_MAX` instead of wrapping to `INT64_MIN` (as on x86). This caused the integer shortcut in `_to_datetime_with_unit` and `sequence_to_td64ns` to misfire for OOB float values like `float(2**63)`, because `np.float64(2**63) == np.int64(INT64_MAX)` evaluates to `True` on ARM (INT64_MAX rounds up to 2**63 in float64).

#64619 fixed the datetime case with a separate OOB pre-check in Python, but left a latent bug in the timedelta path for non-ns units. This PR replaces the pre-check with a tighter fix: an `in_int64_range` guard on the shortcut condition itself, applied consistently to both paths.

Changes:
- **`datetimes.py`**: Replace the 12-line OOB pre-check with a 4-line `in_int64_range` guard on the integer shortcut condition. OOB values now fall through to `cast_from_unit_vectorized` which already has its own OOB check, and the existing `try/except` handles the `errors` parameter. Removes the now-unused `iNaT` import.
- **`timedeltas.py`**: Add the same `in_int64_range` guard to the timedelta integer shortcut, fixing the latent ARM bug for non-ns units.
- **`test_to_timedelta.py`**: Add `test_float_to_timedelta_raise_oob_non_ns` covering the timedelta shortcut path with `unit="s"`.

## Test plan

- [x] Existing `test_float_to_datetime_raise_oob_ns` passes
- [x] Existing `test_float_to_timedelta_raise_oob_ns` passes
- [x] New `test_float_to_timedelta_raise_oob_non_ns` passes
- [x] Full `test_to_datetime.py` and `test_to_timedelta.py` suites pass (1024 passed)
- [ ] ARM CI (ubuntu-24.04-arm, macos-15) passes

🤖 Generated with [Claude Code](https://claude.com/claude-code)

## PR Review Comments

**[user]** on `pandas/core/arrays/timedeltas.py`:

Could we use `np.float64(np.iinfo(np.int64).max/min)` instead of hardcoding the 2**63?

**[user]** on `pandas/core/tools/datetimes.py`:

Same here (and ideally the test)

**[user]** on `pandas/core/tools/datetimes.py`:

updated here, forgot to do it in the test.  for worktree-related reasons updating again is a bit inconvenient ATM

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
