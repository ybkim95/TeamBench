# GH1116_dask_10320: Add missing 'not in' predicate support to `read_parquet` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/dask/dask

## PR Description

`dd.read_parquet` does not currently support filters containing `"not in"` predicates. In fact, if the user passes in something like `filters=[("B", "not in", (1, 2))]`, Dask will return an empty `dd.DataFrame`!

This PR adds basic `"not in"` support to address this bug/oversight.

## PR Review Comments

**[user]** on `dask/dataframe/io/parquet/core.py`:

Should we raise on unhandled operators instead of silently ignoring them?

**[user]** on `dask/dataframe/io/parquet/core.py`:

Ah, yes. I agree that the problem is that we were silently filtering for an "unsupported" operator.  I'll try to make the list of supported operators more explicit.

**[user]** on `dask/dataframe/io/parquet/core.py`:

:tada:

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
