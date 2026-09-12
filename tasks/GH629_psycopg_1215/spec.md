# GH629_psycopg_1215: Add ConnectionPool.drain() method — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/psycopg/psycopg

## PR Description

This method clears all the connection currently in the pool and creates new one. The connections currently given will be closed as soon as returned to the pool.

This method is useful for example when it is necessary to query the database to obtain the oid of an extension type and register an adapter. If a pool is used, the connections already in the pool will have the wrong adapters map (see #1027).

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
