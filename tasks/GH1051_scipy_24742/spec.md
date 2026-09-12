# GH1051_scipy_24742: BUG: stats.linregress return NaN in n=2 cases — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/scipy/scipy

## PR Description

<!-- 
Thanks for contributing a pull request! Please ensure that
your PR satisfies the checklist before submitting:
https://scipy.github.io/devdocs/dev/contributor/development_workflow.html#checklist-before-submitting-a-pr

Also, please name and describe your PR as you would write a
commit message:
https://scipy.github.io/devdocs/dev/contributor/development_workflow.html#writing-the-commit-message.
However, please only include an issue number in the description, not the title,
and please ensure that any code names containing underscores are enclosed in backticks.

Depending on your changes, you can skip CI operations and save time and energy: 
https://scipy.github.io/devdocs/dev/contributor/continuous_integration.html#skipping

Note that we are a team of volunteers; we appreciate your
patience during the review process.

Again, thanks for contributing!
-->

#### Reference issue
Closes gh-24684

#### What does this implement/fix?
This PR updates `stats.linregress` to return `NaN` for `pvalue`, `stderr` and `intercept_stderr` when the input contains exactly two points. Previously, the function explicitly overrode these values to be `0.0`, however, with only two data points, there are zero residual degrees of freedom, making the estimation of residual variance undefined.

#### Additional information
<!--Any additional information you think is important.-->

#### AI Generation Disclosure
No AI.

## PR Review Comments

**[user]** on `scipy/stats/tests/test_stats.py`:

This test should run for different array types
```suggestion
    def test_linregress_two_points_nan_inference(xp):
        # Test for  gh-24684
        x = xp.asarray([0., 1.])
        y = xp.asarray([0., 1.])

        res = stats.linregress(x, y)

        NaN = xp.asarray(xp.nan)
        xp_assert_equal(res.pvalue, NaN)
        xp_assert_equal(res.stderr, NaN)
        xp_assert_equal(res.intercept_stderr, NaN)

        # Point estimates should still be correct
        assert res.slope == 1
        assert res.intercept == 0
```

**[user]** on `scipy/stats/_stats_py.py`:

Why was this changed? https://github.com/data-apis/array-api-compat/issues/271?
This doesn't look like it will preserve dtype anymore because `xp.zeros` produces the default float, which could upcast lower working precision.
Note that `xp.nan` is a Python float, like `math.nan`.

**[user]** on `scipy/stats/_stats_py.py`:

What happens if you remove the special case? Isn't NumPy the only backend that emits warnings, which you can suppress with `np.errstate` (*if* we think they are uninformative). The advantage is that then MArray doesn't need a special case.

**[user]** on `scipy/stats/tests/test_stats.py`:

```suggestion
        # Test for gh-24684
```
If tests are passing, I'll commit with `[skip ci]` and merge.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
