# GH912_sktime_4425: [BUG] temporarily skip `test_predict_quantiles` for `VAR` due to known sporadic bug #4420 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/sktime/sktime/issues/1234
- Repo: https://github.com/sktime/sktime

## Issue Description

Fixes #1043 

Removed methods load_UCR_UEA_dataset & _load_dataset from datasets/base.py and moved them to utils/data_io.py

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
