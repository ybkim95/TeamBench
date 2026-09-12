# GH706_httpx_3672: Server connection handling. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/encode/httpx

## PR Description

* Add `HTTPParser.keep_alive`.
* Server... always read request to completion on keep alives.
* `HTTPParser.complete` -> `.reset`
* Close streams on server exit.
* Don't raise `KeyboardException` on server exit.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
