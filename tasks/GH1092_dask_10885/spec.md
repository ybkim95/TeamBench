# GH1092_dask_10885: Pickle da.argwhere and da.count_nonzero — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/dask/dask

## PR Description

Fix serialization of da.argwhere and da.count_nonzero:

```
_pickle.PicklingError: Can't pickle <ufunc '_isnonzero_vec (vectorized)'>: attribute lookup _isnonzero_vec (vectorized) on __main__ failed
```

## PR Review Comments

**[user]** on `dask/array/routines.py`:

Why the rewrite here?

**[user]** on `dask/array/routines.py`:

1. This looked slightly more compact and readable IMHO
2. Best practice of not changing the type of a variable after initial assignment

Ultimately it is cosmetic.

**[user]** on `dask/array/routines.py`:

I think lambdas cause issues in serialisation cost on the scheduler, so I would prefer rolling this back if it's only cosmetic, not objecting to fixing the assignment issue though

**[user]** on `dask/array/routines.py`:

reverted

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
