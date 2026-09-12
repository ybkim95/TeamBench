# GH875_great_expectati_1616: [BUGFIX] fixed bug in rounding of mostly argument to nullity expectations produced by the BasicSuiteBuilderProfiler — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/great-expectations/great_expectations/issues/123
- Repo: https://github.com/great-expectations/great_expectations

## Issue Description

Prefer `from __future__ import division` to `1.*x/y`

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Done inline during improve_partitions push.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
