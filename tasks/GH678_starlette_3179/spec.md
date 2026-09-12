# GH678_starlette_3179: Use `bytearray` for field accumulation in `FormParser` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/Kludex/starlette

## PR Description

## Summary

- Replace immutable `bytes` concatenation (`+=`) with mutable `bytearray.extend()` in `FormParser.parse()` to avoid O(n²) copying when accumulating field names and values.
- No behavioral or API change - `bytearray.decode()` produces the same `str` as `bytes.decode()`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
