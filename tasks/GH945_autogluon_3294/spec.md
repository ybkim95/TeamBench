# GH945_autogluon_3294: Fix `predict_multi` crashing when `inverse_transform=False` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/autogluon/autogluon

## PR Description

*Issue #, if available:*

*Description of changes:*
- Fix `predict_multi` crashing when `inverse_transform=False, as_pandas=True`
- Fix `predict_proba_multi` crashing when `inverse_transform=False, as_pandas=True` and dropped classes exist.
- Unified post-processing code between `predict` and `predict_multi`.
- Unified post-processing code between `predict_proba` and `predict_proba_multi`.
- Added additional unit tests for `predict_multi` and `predict_proba_multi`

By submitting this pull request, I confirm that you can use, modify, copy, and redistribute this contribution, under the terms of your choice.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
