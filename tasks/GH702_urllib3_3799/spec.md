# GH702_urllib3_3799: Add Iterable[str] to input body type — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/urllib3/urllib3

## PR Description

This PR addresses #3798 by adding `Iterable[str]` to the accepted input types for bodies. This was the behavior documented prior to types being added (and is still the documented behavior), so this change is largely cosmetic.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
