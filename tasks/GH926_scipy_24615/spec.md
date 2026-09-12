# GH926_scipy_24615: BUG: ndimage: fix aliasing in _init_causal_reflect for small arrays — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/scipy/scipy

## PR Description

#### Reference issue

Closes gh-24550

#### What does this implement/fix?

The causal reflect initialization in `_init_causal_reflect` accumulated
the sum directly into `c[0]`, but on the last loop iteration `c[n-1-i]`
aliases `c[0]`, reading the already-modified value. The error scales with
z^(2n), so it's negligible for large arrays but significant when n is
small (2 or 3), which happens with multi-channel images.

The fix accumulates into a local variable instead of mutating `c[0]`
during the loop.

#### Additional information

Regression test added in `test_splines.py` that verifies the spline
filter matrix identity for small n with reflect mode.

## PR Review Comments

**[user]** on `scipy/ndimage/tests/test_splines.py`:

Ignoring the older code already in this file, it would likely be preferable to use i.e., `assert_allclose()` per docs at: https://numpy.org/doc/stable/reference/generated/numpy.testing.assert_almost_equal.html. Since this is an `xp` test case, I suppose `xp_assert_close()` may be even more appropriate.

It would probably also make sense to have the "actual" value come first as documented (i.e., `eye` is the expected result/second argument).

Since `map_coordinates()` itself is a public function, would it make sense to have a regression test on it directly as well? It looks like the test case the user provided at https://github.com/scipy/scipy/issues/24550#issuecomment-3914338813 does indeed fail before and pass after this patch, although that test case uses `map_coordinates` for both the `actual` and `expected` values, which is probably also suboptimal.

**[user]** on `scipy/ndimage/tests/test_splines.py`:

Thanks for the review. Switched to xp_assert_close with actual first, and added a map_coordinates test in test_interpolation.py that compares single-channel vs multi-channel output on random data.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
