# GH684_starlette_3144: Avoid mutating `FileResponse` headers on range requests — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/Kludex/starlette

## PR Description

`FileResponse` mutates `self.headers` when handling range requests, making the instance unusable for subsequent calls. Copy `raw_headers` into a local `MutableHeaders` before setting `content-range`, `content-type`, and `content-length`.

Credit to [user].

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
