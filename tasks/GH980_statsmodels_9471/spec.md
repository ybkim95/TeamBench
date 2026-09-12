# GH980_statsmodels_9471: Fix formula eval depth in select models — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/statsmodels/statsmodels/issues/9047
- Repo: https://github.com/statsmodels/statsmodels

## Issue Description

- [x] closes #9037
- [x] tests added / passed. 
- [x] properly formatted commit message. See 
      [NumPy's guide](https://docs.scipy.org/doc/numpy-1.15.1/dev/gitwash/development_workflow.html#writing-the-commit-message). 

This PR fixes the formula environment for the conditional logit and Poisson, the proportional hazards model, GEE, and QIF.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Overall PR looks good.  Do you know if other formulas suffer, or is this the full extent fo the problem?

### Comment 2 ([user]):

There are a few linting issues that need to be fixed.  You can ignore MICE errors (needs a deep dive).

### Comment 3 ([user]):

The problem appears in several other `from_formula`s, but gets more complicated because multiple formulas are used. For example, `BetaModel` takes both the main formula and an optional `exog_precision_formula`. That second formula isn't parsed with an eval environment, so I expect that it would similarly grab the environment from a statsmodels file rather than the user's environment.

I was trying to sidestep those cases for my first contribution (sorry about the linting error) but I just noticed `GEE.from_formula` has an optional second formula too. If you don't mind a longer PR, I can extend the fix to those other implementations and their other formulas.

What do you think about putting `eval_env` into the method signatures directly? I'm not sure if it would have to be a keyword-only argument to avoid breaking possible uses.

### Comment 4 ([user]):

I guess this conflicts with formulaic merge

[user] 
Is there anything left in this PR that needs to be merged?

### Comment 5 ([user]):

Leave it to me.  I'll add the test and see if it causes any problems.

### Comment 6 ([user]):

Updated fix in #9471   Found a few more cases where this fix matters.  Thanks for the PR.  Very helpful.

## PR Review Comments

**[user]** on `statsmodels/miscmodels/tests/test_ordinal_model.py`:

## Unused local variable

Variable times_two is not used.

[Show more details](https://github.com/statsmodels/statsmodels/security/code-scanning/2804)

**[user]** on `statsmodels/othermod/tests/test_beta.py`:

## Unused local variable

Variable times_two is not used.

[Show more details](https://github.com/statsmodels/statsmodels/security/code-scanning/2802)

**[user]** on `statsmodels/regression/tests/test_lme.py`:

## Unused local variable

Variable times_two is not used.

[Show more details](https://github.com/statsmodels/statsmodels/security/code-scanning/2803)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
