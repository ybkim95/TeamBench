# GH966_pymc_7890: Fix `independent_rvs` determination in `vectorize_over_posterior` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pymc-devs/pymc/issues/7889
- Repo: https://github.com/pymc-devs/pymc

## Issue Description

### Description

When a computational graph has random variable Ops that are not model freeRVs, but are conditioned on them, `vectorize_over_posterior` misinterprets them as `independent_rvs` and replaces them with `change_dist_size`. This makes all of the freeRV ancestors as they were defined in their prior, instead of replacing their values with the draws from the posterior. Take this example:

```python
import pymc as pm
import pytensor

with pm.Model() as model:
    a = pm.Normal("a")
    b = pm.Normal.dist(a)
    c = b + 1
    d = pm.Normal.dist(c)
    idata = pm.sample_prior_predictive(100, var_names=["a"])
    idata.add_groups({"posterior": idata.prior})
_, _, vectorized_no_intermediate = vectorize_over_posterior(
    outputs=[b, c, d],
    posterior=idata.posterior,
    input_rvs=[a],
    allow_rvs_in_graph=True,
)
[vectorized_intermediate_rvs] = vectorize_over_posterior(
    outputs=[d],
    posterior=idata.posterior,
    input_rvs=[a],
    allow_rvs_in_graph=True,
)
pytensor.dprint([vectorized_no_intermediate, vectorized_intermediate_rvs], print_shape=True)
```

This prints:
```python
normal_rv{"(),()->()"}.1 [id A] shape=(1, 100)
 ├─ RNG(<Generator(PCG64) at 0x14F6E9460>) [id B]
 ├─ NoneConst{None} [id C]
 ├─ Add [id D] shape=(1, 100)
 │  ├─ normal_rv{"(),()->()"}.1 [id E] shape=(1, 100)
 │  │  ├─ RNG(<Generator(PCG64) at 0x14F6E9B60>) [id F]
 │  │  ├─ NoneConst{None} [id C]
 │  │  ├─ a{[[ 0.03487 ... 0263003 ]]} [id G] shape=(1, 100)
 │  │  └─ ExpandDims{axes=[0, 1]} [id H] shape=(1, 1)
 │  │     └─ 1.0 [id I] shape=()
 │  └─ ExpandDims{axes=[0, 1]} [id J] shape=(1, 1)
 │     └─ 1 [id K] shape=()
 └─ ExpandDims{axes=[0, 1]} [id L] shape=(1, 1)
    └─ 1.0 [id M] shape=()
normal_rv{"(),()->()"}.1 [id N] shape=(1, 100)
 ├─ RNG(<Generator(PCG64) at 0x14F6E9460>) [id B]
 ├─ NoneConst{None} [id C]
 ├─ Add [id O] shape=(1, 100)
 │  ├─ normal_rv{"(),()->()"}.1 [id P] shape=(1, 100)
 │  │  ├─ RNG(<Generator(PCG64) at 0x158AAF140>) [id Q]
 │  │  ├─ [  1 100] [id R] shape=(2,)
 │  │  ├─ ExpandDims{axes=[0, 1]} [id S] shape=(1, 1)
 │  │  │  └─ normal_rv{"(),()->()"}.1 [id T] shape=() 'a'
 │  │  │     ├─ RNG(<Generator(PCG64) at 0x14F6E8AC0>) [id U]
 │  │  │     ├─ NoneConst{None} [id C]
 │  │  │     ├─ 0 [id V] shape=()
 │  │  │     └─ 1.0 [id W] shape=()
 │  │  └─ ExpandDims{axes=[0, 1]} [id X] shape=(1, 1)
 │  │     └─ 1.0 [id I] shape=()
 │  └─ ExpandDims{axes=[0, 1]} [id Y] shape=(1, 1)
 │     └─ 1 [id K] shape=()
 └─ ExpandDims{axes=[0, 1]} [id Z] shape=(1, 1)
    └─ 1.0 [id M] shape=()
```

where the `vectorized_no_intermediate` correctly replaces `a` with the draws from the posterior, whereas, `vectorized_intermediate_rvs` uses a changed size version of `b`, which keeps the old scalar `a` random variable in the graph.

## PR Review Comments

**[user]** on `pymc/sampling/forward.py`:

outputs / needed_rvs / independent_rvs are also the `blockers` store than in an intermediate variable?

**[user]** on `pymc/sampling/forward.py`:

filter `rv not in needed_rvs` already in the list comp that starts this loop?

**[user]** on `tests/sampling/test_forward.py`:

Assuming there should only be one match:
```suggestion
    [a_ancestor1] = get_var_by_name([vectorized_no_intermediate], "a")
    [a_ancestor2] = get_var_by_name([vectorized_intermediate_rvs], "a")
```

**[user]** on `pymc/sampling/forward.py`:

NIT: This could be a set, ancestors will convert it to one anyway.
NIT: This could be created incrementally, you're just adding independent_rvs in the loop

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
