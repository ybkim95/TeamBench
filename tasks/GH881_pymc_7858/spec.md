# GH881_pymc_7858: Fix bug with pickling PointFunc — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pymc-devs/pymc/issues/7857
- Repo: https://github.com/pymc-devs/pymc

## Issue Description

### Description

This error came up in (withheld: the upstream fix is not part of the task). It is caused by `PointFunc` recursively trying to access `self.f` during unpickling. MWE:

```py
import pymc as pm
with pm.Model() as m:
    x = pm.Categorical('x', logit_p=[1., 1., 1., 1.]))
    idata = pm.sample(step=pm.CategoricalGibbsMetropolis([x]), mp_ctx='spawn')
```

A simple fix would add a check that f has been set inside `PointFunc.__getattr__`

## PR Review Comments

**[user]** on `pymc/pytensorf.py`:

Nah let's just take out the magic, and replace by a a dprint method that does `self.f.dprint`, that's the thing I wanted anyway

**[user]** on `tests/step_methods/test_metropolis.py`:

Why is this specific to binary gibbs? That's the only one using PointFunc?

We should test spawning a PointFunc instead or this test won't be a regression test if binary gibbs changes to not using PointFunc

**[user]** on `tests/step_methods/test_metropolis.py`:

no idea why it's these functions. model.compile_xxx returns a PointFunc, so everyone uses them, but only these 3 samplers trigger the error (I tried most of them)

**[user]** on `tests/step_methods/test_metropolis.py`:

Most samplers build their own function on raveled inputs and don't use the wrapper PointFunc for performance

**[user]** on `tests/test_pytensorf.py`:

Just to be sure this failed before?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
