# GH1217_featuretools_2182: Fix Woodwork 0.17.0 Integration Test Failures — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/alteryx/featuretools

## PR Description

-- Fix `bool` * `numeric`  test failure in `test_transform_features.py` by setting `numeric` column to `Double` type.
-- Set logical type for `num_square_feet` in `stores` dataframe when creating `mock_ecommerce_entityset`

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
