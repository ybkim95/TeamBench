# GH1130_sktime_6713: [MNT] skip failing test `test_wrapper_series_mtype` on `gluonts` datatype — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/sktime/sktime

## PR Description

This PR skips the failing test `test_wrapper_series_mtype` on the `gluonts` mtype `gluonts_ListDataset_series`.

This needs to be fixed, but is skipped to enable the release.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
