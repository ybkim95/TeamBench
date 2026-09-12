# GH705_httpx_3690: Add `.wait_ready` to parser for clean server disconnects — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/encode/httpx

## PR Description

Add `.wait_ready()` to `HTTPParser`...

We need this in order to differentiate between clean disconnects at the start of a new request/response cycle, rather than a `ProtocolError` while calling `recv_method_line()`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
