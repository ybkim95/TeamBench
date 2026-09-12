# GH1131_sktime_4442: [MNT] except `VECM` from `test_predict_quantiles` due to sporadic failures — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/sktime/sktime

## PR Description

Excepts `VECM` from `test_predict_quantiles` due to sporadic failures of the current test (quantile prediction monotonocity), see https://github.com/sktime/sktime/issues/4431

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
