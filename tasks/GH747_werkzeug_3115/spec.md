# GH747_werkzeug_3115: undeprecated CSP report-uri for now — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pallets/werkzeug

## PR Description

`report-uri` is still widely used and supported by browsers. `report-to` requires setting a feature flag on Firefox.

continues #3114

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
