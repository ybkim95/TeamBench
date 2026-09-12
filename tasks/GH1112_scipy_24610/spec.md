# GH1112_scipy_24610: MAINT: stats.make_distribution: fix some issues with `rv_generic`s + array shape parameters — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/scipy/scipy

## PR Description

#### Reference issue
gh-22040

#### What does this implement/fix?
In gh-22040, I wrote that something about "beta, genextreme, gengamma, t, tukeylambda" wasn't working work with `make_distribution` when the shape parameters were 1D arrays. This fixes the problems I could see and extends the test of `make_distribution` w/ `rv_generic`s to include array shape parameters.

#### Additional information
The `make_distribuiton` test is pretty slow already for some distributions. Tests for those distributions are skipped unless `SCIPY_XSLOW=1`, but I try to always run with `SCIPY_XSLOW=1` locally. I'm not sure the additional regression test coverage is worth the time it takes to run the tests, even when `SCIPY_XSLOW=1` is selected. I would prefer to comment out portion of the tests that makes the shape parameters arrays.

## PR Review Comments

**[user]** on `scipy/stats/_discrete_distns.py`:

Without this dtype conversion, I get failures because NumPy won't convert floats to ints.
With this conversion, I get a failure in CI on 32-bit because NumPy won't convert int64 to int32. 
Should I take advantage of NumPy's flexibility with dtype specifications and just set `dtype=int`?

**[user]** on `scipy/stats/_continuous_distns.py`:

Apparently the old infrastructure doesn't convert lists to arrays before passing them to `_get_support`.

**[user]** on `scipy/stats/_continuous_distns.py`:

This code wasn't vectorized. I guess the old infrastructure calls `_munp` for each element of `c` separately, but the new one expects it to be vectorized, so this vectorizes it.

**[user]** on `scipy/stats/_continuous_distns.py`:

This isn't need anymore because it is taken care of by the asymptotic approximation.

**[user]** on `scipy/stats/_continuous_distns.py`:

Like `_munp`, I guess the old infrastructure loops over elements of `lam`, whereas the new infrastructure expects `_entropy` to be vectorized. I could have used `tanhsinh` to vectorize this, but I don't want to mix in `tanhsinh` with the old infrastructure.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
