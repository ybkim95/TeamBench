# GH1000_numpy_19869: BUG: ensure np.median does not drop subclass for NaN result. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/numpy/numpy

## PR Description

Currently, np.median is almost completely safe for subclasses, except
if the result is NaN.  In that case, it assumes the result is a scalar
and substitutes a NaN with the right dtype.  This PR fixes that, since
subclasses like astropy's Quantity generally use array scalars to
preserve subclass information such as the unit.

See https://github.com/astropy/astropy/issues/12165 (note that of course we can work around this via `__array_function__`, but it seems a genuine oversight in the code).

## PR Review Comments

**[user]** on `numpy/lib/tests/test_function_base.py`:

These tests failed for the cases that include `np.nan`

**[user]** on `numpy/lib/utils.py`:

This rewrites more than strictly needed, but for performance it seemed to make sense to start with only doing anything if there was an actual `nan`. Somewhat surprisingly, this stanza is quite fast even for the scalar case:
```
In [19]: %timeit np.count_nonzero(np.True_.ravel()) > 0
1.07 µs ± 2.14 ns per loop (mean ± std. dev. of 7 runs, 1000000 loops each)
In [21]: b = np.array(True)

In [22]: %timeit b.ndim == 0 and np.True_ == True
776 ns ± 6.61 ns per loop (mean ± std. dev. of 7 runs, 1000000 loops each)
```

**[user]** on `numpy/lib/utils.py`:

What happened to `out`?

**[user]** on `numpy/lib/utils.py`:

I looked at the two places where this code is used, and one always has `result is out` if `out` is given (which was already assumed to be the case for when `result` is an array...). 

But you are right that perhaps it is better to then just change the call sequence to remove `out` and change it accordingly where it is used. Shall I do that?

**[user]** on `numpy/lib/utils.py`:

Thanks for checking that. If `out` isn't used it would be best to remove it and document the assumptions about how the function should be used.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
