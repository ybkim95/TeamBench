# GH1065_gpytorch_2132: fix custom dtype_value_context setting — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/cornellius-gp/gpytorch

## PR Description

Previously, setting custom values in `dtype_value_context` was broken because `dtype_value_context.value` requires a `dtype` argument and no `dtype` argument was provided in the calls in `dtype_value_context.__init__`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
