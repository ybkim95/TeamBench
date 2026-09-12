# GH414_aiohttp_12249: Tokenize Connection header values in Python HTTP parser — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/aio-libs/aiohttp

## PR Description

## What do these changes do?

Align the pure-Python HTTP request parser with the C parser for `Connection` handling.

- Parse `Connection` from all field lines (`getall`) instead of only the first value.
- Split comma-separated values into tokens and compare case-insensitively.
- Apply token-based semantics for `close`, `keep-alive`, and `upgrade`.
- Add regression tests for comma-separated and repeated `Connection` values.

## Are there changes in behavior for the user?

Yes, for requests with multi-value/repeated `Connection` headers.

- `Connection: keep-alive, upgrade` + `Upgrade: websocket` now upgrades in the Python parser.
- `Connection: close, keep-alive` now results in `should_close=True` in the Python parser.
- Single-token behavior is unchanged.

## Is it a substantial burden for the maintainers to support this?

No. This is a small parser-consistency fix with focused regression coverage and no new dependencies.

## Related issue number

N/A (security report).

## Checklist

- [x] I think the code is well written
- [x] Unit tests for the changes exist
- [ ] Documentation reflects the changes
- [x] If you provide code modification, please add yourself to `CONTRIBUTORS.txt`
- [x] Add a new news fragment into the `CHANGES/` folder

## PR Review Comments

**[user]** on `aiohttp/http_parser.py`:

Note to self: Remove .getall() in #7679

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
