# GH1071_dask_11656: Fix projection when columns are numpy scalars — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/dask/dask

## PR Description

While updating RAPIDS to align with the recent dask-expr migration, I found that column projection after a default `from_dask_array` operation was behaving strangely (for both the "cudf" and "pandas" backends).

I'm proposing one simple solution here - Other suggestions are welcom.

## PR Review Comments

**[user]** on `dask/dataframe/dask_expr/_util.py`:

it looks like this disables list comparisons?

**[user]** on `dask/dataframe/dask_expr/_util.py`:

It checks that both scalars, or both are **not** scalars. Otherwise, we don't need to compare.

I don't love this logic either, but nothing elegant jumped out at me :/

**[user]** on `dask/dataframe/dask_expr/_util.py`:

can you just check if both are scalars and then convert? Otherwise fall back to ==

If we have numpy array in there, then this **should** raise

**[user]** on `dask/dataframe/dask_expr/_util.py`:

>If we have numpy array in there, then this should raise

Yeah, that totally makes sense.

**[user]** on `dask/dataframe/dask_expr/_util.py`:

>can you just check if both are scalars and then convert? Otherwise fall back to ==

We need to account for the comparison between a `np.int64(0)` and a list like `[0, 1, 2]`. The other alternatives are:

- We validate the scalar argument in `FrameBase.__getitem__` and extract the python value
- We declare that this isn't actually a bug, and that the user now needs to do `df[df.columns[0].item()]`

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
