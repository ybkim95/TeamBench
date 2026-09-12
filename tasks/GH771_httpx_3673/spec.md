# GH771_httpx_3673: Connection resets — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/encode/httpx

## PR Description

* `HTTPParser.complete` -> `.reset`.
* Add `HTTPParser.is_keepalive` API.
* Clean exits on `KeyboardInterupt`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
