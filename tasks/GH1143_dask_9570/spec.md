# GH1143_dask_9570: Avoid `pandas` constructors in `dask.dataframe.core` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/dask/dask

## PR Description

There are many places in dask.dataframe where `pd.DataFrame`/`pd.Series` constructors are used explicitly. This PR proposes the addition of `serial_frame_constructor` and `serial_series_constrictor` utilities that take in an optional `like` parameter to determine which `DataFrame`/`Series` constructor to use (i.e. `pandas` or `cudf`). Default is `pandas.DataFrame` and `pandas.Series`.

The optional `like` argument is currently expected to be a serial `DataFrame`, serial `Series`, `DataFrame` collection, or `Series` collection.  It may also make sense to handle a numpy/cupy Array or Array collection (along the lines of [user]'s suggestion in [#11889](https://github.com/rapidsai/cudf/issues/11889)).  Howeer, that feature will probablty require the addition of a new `array_to_frame` diispatch as well (or something similar).

- [x] Closes [#11889](https://github.com/rapidsai/cudf/issues/11889)
- [ ] Tests added / passed
- [ ] Passes `pre-commit run --all-files`

## PR Review Comments

**[user]** on `dask/dataframe/utils.py`:

Is there ever a time we'll not specify `like`? If not, let's make it a positional argument

**[user]** on `dask/dataframe/utils.py`:

Similar comment here

**[user]** on `dask/dataframe/utils.py`:

I believe `_Frame._constructor` already covers this case

**[user]** on `dask/dataframe/utils.py`:

Would `is_series_like(...)` and `Series._constructor_expanddim` work here instead?

**[user]** on `dask/dataframe/core.py`:

What is `data` here? Can we get the DataFrame type from that?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
