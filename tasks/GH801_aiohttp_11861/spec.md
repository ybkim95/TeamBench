# GH801_aiohttp_11861: fix(connector): propagate proxy headers on connection reuse (#11777) — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/aio-libs/aiohttp

## PR Description

(cherry picked from commit 7bbf17d09d5f87b93022d340e39d53f386d5d485)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
