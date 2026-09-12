# GH1117_dask_10043: Avoid using `dd.shuffle` in groupby-apply — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/dask/dask

## PR Description

Some RAPIDS developers have been seing p2p errors while using the "cudf" backend (which does not support the p2p method just yet). This PR tweaks `_GroupBy._shuffle` to effectively use `self.obj.shuffle` instead of `dd.shuffle` to make sure `dask_cudf` has the opportunity to set the appropriate default algorithm.

cc [user]

## PR Review Comments

**[user]** on `dask/dataframe/tests/test_groupby.py`:

Looks like #10025 was closed but this xfail line is passing CI - Not sure if this line should be removed?

**[user]** on `dask/dataframe/tests/test_groupby.py`:

Ah, never mind - There are indeed `[XPASS(strict)]` failures being ignored for the pyarrow tests. I removed this line.

**[user]** on `dask/dataframe/groupby.py`:

Note that we don't actually **want** to validate/process `self.by` and define this `by` variable, because `shuffle` is already designed to do this better.  I say "better", because it will be able to reduce the overall memory usage of a task-based shuffle when column names are specified (without affecting p2p performance).

**[user]** on `dask/dataframe/shuffle.py`:

Again - If we will ultimately use a task-based shuffle, we want to avoid the memory overhead of creating/assigning a new column by going into the `if`-block below. We cannot do this if `shuffle` is still `None`.

**[user]** on `dask/dataframe/groupby.py`:

I don't quite understand this comment

> because shuffle is already designed to do this better

Can you point me to where this is happening?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
