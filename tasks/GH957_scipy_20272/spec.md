# GH957_scipy_20272: BUG: optimize: fix incorrect variable assignment in `_trustregion_exact.py` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/scipy/scipy

## PR Description

#### Reference issue
Fixes gh-20244

#### What does this fix?
Result of cholesky factorization in disregarded in `IterativeSubproblem.solve()`.
These changes use the result on successful factorization.

## PR Review Comments

**[user]** on `scipy/optimize/tests/test_trustregion_exact.py`:

```suggestion
    def test_gh20244(self):
```

**[user]** on `scipy/optimize/tests/test_trustregion_exact.py`:

```suggestion
        assert_assert_allclose(p, [-0.77472957,  0.63229272])
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
