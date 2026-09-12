# GH982_statsmodels_9398: BUG: Ensure hessian is skipped — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/statsmodels/statsmodels/issues/9181
- Repo: https://github.com/statsmodels/statsmodels

## Issue Description

The `skip_hessian` option did not work in ConditionalLogit.fit() because the ConditionalResults function tried to retrieve cov_params() from LikelihoodModel.fit() results.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hello [user]! Thanks for opening this PR. We checked the lines you've touched for [PEP 8](https://www.python.org/dev/peps/pep-0008) issues, and found:

* In the file [`statsmodels/discrete/conditional_models.py`](https://github.com/statsmodels/statsmodels/blob/c51e9cea20aebc4dd7a8e0d71fb6d3032465ea37/statsmodels/discrete/conditional_models.py):

> [Line 124:1](https://github.com/statsmodels/statsmodels/blob/c51e9cea20aebc4dd7a8e0d71fb6d3032465ea37/statsmodels/discrete/conditional_models.py#L124): [W293](https://duckduckgo.com/?q=pep8%20W293) blank line contains whitespace

### Comment 2 ([user]):

the fix looks correct to me, but I'm not familiar with the internals of these models.

Thanks for finding this and the PR


In general, `skip_hessian` was mainly introduced for internal use to avoid computing the hessian or cov_params more than once. I guess it's never directly unit tested.

### Comment 3 ([user]):

That makes sense. For researchers, it can be a useful option for inspecting coefficient values in large models without having to compute the Hessian every time -- which can take many times longer.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
