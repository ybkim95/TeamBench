# GH1114_statsmodels_9739: BUG: Fix patsy eval_env handling in FormulaManager and add parametrized re… — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/statsmodels/statsmodels

## PR Description

This PR fixes a bug in FormulaManager.get_matrices where a normalized evaluation environment (_eval_env) was constructed for the patsy backend but not passed through to patsy.dmatrix / patsy.dmatrices. As a result, dict-based eval_env inputs (as documented) were ignored and could raise a TypeError.

The fix ensures the normalized _eval_env is consistently used when calling patsy, restoring correct handling of dict-provided evaluation contexts and aligning behavior with the formulaic backend.

A parametrized regression test is added to cover dict-based eval_env usage and to prevent future regressions.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
