# GH676_starlette_3142: Set `Content-Type` instead of `Content-Range` on multi-range responses — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/Kludex/starlette

## PR Description

Set `Content-Type` to `multipart/byteranges; boundary=...` and leave `Content-Range` unset on multi-range responses per [RFC 9110 §14.6](https://httpwg.org/specs/rfc9110.html#partial.multipart).

Extracted from #3105.

Co-authored-by: Victor Westerhuis <[email redacted]>

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
