# GH907_autogluon_4272: [tabular] Fix LightGBM quantile predict_proba dtype — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/autogluon/autogluon/issues/4270
- Repo: https://github.com/autogluon/autogluon

## Issue Description

Related: #4268 

Currently, all models return a np.ndarray for predict_proba, while LightGBM returns a pd.DataFrame (for quantile problem type).

This can cause issues such as in #4268. It is better to have a consistent return format. This should also be part of unit tests

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
