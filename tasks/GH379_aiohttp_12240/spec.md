# GH379_aiohttp_12240: Reject duplicate singleton headers in C extension parser — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/aio-libs/aiohttp

## PR Description

## What do these changes do?

Add duplicate singleton header validation to the C extension HTTP parser (`_http_parser.pyx`) to match the existing pure Python parser behavior.

The C extension parser now rejects requests containing duplicate RFC 9110 singleton headers (`Host`, `Content-Type`, `Content-Length`, `Content-Location`, `Content-Range`, `ETag`, `Max-Forwards`, `Server`, `Transfer-Encoding`, `User-Agent`) with a `BadHttpMessage` error, just as the pure Python parser already does.

## Are there changes in behavior for the user?

Yes. HTTP requests with duplicate singleton headers that were previously accepted (and silently used the first value) are now rejected with a `400 Bad Request`. This is the **correct behavior** per RFC 9110 §5.5 and matches what the pure Python parser already enforces.

## Is it a substantial burden for the maintainers to support this?

No. The change mirrors existing logic from the pure Python parser (`http_parser.py:500-514`) into the C extension parser. It is a small, focused security fix with no new dependencies or architectural changes.

## Related issue number

Align C and python implementations

## Checklist

- [x] I think the code is well written
- [x] Unit tests for the changes exist
- [ ] Documentation reflects the changes
- [ ] If you provide code modification, please add yourself to `CONTRIBUTORS.txt`
- [x] Add a new news fragment into the `CHANGES/` folder

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
