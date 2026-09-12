# GH968_pymc_7637: Fix MCMC non-deterministic seeding with Generators — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pymc-devs/pymc/issues/7612
- Repo: https://github.com/pymc-devs/pymc

## Issue Description

### Description

This was revealed in (withheld: the upstream fix is not part of the task)

```python
import numpy as np
import pymc as pm

with pm.Model() as m:
    x = pm.Normal("x")

    post1 = pm.sample(tune=10, draws=10, random_seed=np.random.default_rng(42)).posterior
    post2 = pm.sample(tune=10, draws=10, random_seed=np.random.default_rng(42)).posterior
assert post1.equals(post2), (post1["x"].mean().item(), post2["x"].mean().item())
# AssertionError: (0.22006495904628473, -0.31090965213192406)
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

[user] seems to be caused by (withheld: the upstream fix is not part of the task)

### Comment 2 ([user]):

This might be fixed by the second, third, and fourth commits from #7540. This might be caused by that bug from numpy<2.0 where the random generator was not copied properly.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
