# GH1153_sktime_3139: [MNT] temporarily exclude `RandomShapeletTransform` from tests — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/sktime/sktime

## PR Description

Excludes the failing `RandomShapeletTransform` from tests until we know what is going on.

See #3138 for the failure.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
