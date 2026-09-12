# GH855_psycopg_1227: Fix server cursor iteration — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/psycopg/psycopg/issues/1226
- Repo: https://github.com/psycopg/psycopg

## Issue Description

```
n=0
with connection.cursor(name="server-side-cursor") as cursor:
  cursor.itersize = 1000
  for _ in cursor.execute("select generate_series(1,10000)"):
    n=n+1
print(n)
```

Using version 3.2.13 this prints 10000, using 3.3 this prints 1000 instead

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Issue confirmed. Pretty serious: trying to put together a fix soon.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
