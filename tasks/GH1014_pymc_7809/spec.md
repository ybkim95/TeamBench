# GH1014_pymc_7809: Only add `dim_length` shared variable when adding a new coordinate — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pymc-devs/pymc/issues/7808
- Repo: https://github.com/pymc-devs/pymc

## Issue Description

### Describe the issue:

`Model.add_coord` can add multiple `dim_length` shared variables for the same dimension, which can lead to serious problems down the line.

### Reproduceable code example:

```python
import pymc as pm
from pytensor.graph.basic import get_var_by_name

coord = {"dim1": ["a", "b", "c"]}
with pm.Model(coords=coord) as m:
    a = pm.Normal("a", dims="dim1")
    with pm.Model(coords=coord) as nested_m:
        b = pm.Normal("b", dims="dim1")
    m.add_coords(coord)
    c = pm.Normal("c", dims="dim1")
    d = pm.Deterministic("d", a + b + c)
d.dprint(print_shape=True)
print(get_var_by_name([d], "dim1"))
```

### Error message:

```shell
Identity [id A] shape=(?,) 'd'
 └─ Add [id B] shape=(?,)
    ├─ Add [id C] shape=(?,)
    │  ├─ normal_rv{"(),()->()"}.1 [id D] shape=(?,) 'a'
    │  │  ├─ RNG(<Generator(PCG64) at 0x15D5A8AC0>) [id E]
    │  │  ├─ MakeVector{dtype='int64'} [id F] shape=(1,)
    │  │  │  └─ dim1 [id G] shape=()
    │  │  ├─ ExpandDims{axis=0} [id H] shape=(1,)
    │  │  │  └─ 0 [id I] shape=()
    │  │  └─ ExpandDims{axis=0} [id J] shape=(1,)
    │  │     └─ 1.0 [id K] shape=()
    │  └─ normal_rv{"(),()->()"}.1 [id L] shape=(?,) 'b'
    │     ├─ RNG(<Generator(PCG64) at 0x15E429700>) [id M]
    │     ├─ MakeVector{dtype='int64'} [id N] shape=(1,)
    │     │  └─ dim1 [id O] shape=()
    │     ├─ ExpandDims{axis=0} [id P] shape=(1,)
    │     │  └─ 0 [id Q] shape=()
    │     └─ ExpandDims{axis=0} [id R] shape=(1,)
    │        └─ 1.0 [id S] shape=()
    └─ normal_rv{"(),()->()"}.1 [id T] shape=(?,) 'c'
       ├─ RNG(<Generator(PCG64) at 0x15E4299A0>) [id U]
       ├─ MakeVector{dtype='int64'} [id V] shape=(1,)
       │  └─ dim1 [id W] shape=()
       ├─ ExpandDims{axis=0} [id X] shape=(1,)
       │  └─ 0 [id Y] shape=()
       └─ ExpandDims{axis=0} [id Z] shape=(1,)
          └─ 1.0 [id BA] shape=()
(dim1, dim1, dim1)
```

### PyMC version information:

Current main

### Context for the issue:

This problem popped up because `freeze_dims_and_data` was not replacing all `SharedVariable` dim length variables in the model. When digging deeper, I found that this was happening because there were multiple dimension lengths that had different identities but shared the same name. I'm not sure why `freeze_dims_and_data` didn't still work though.

## PR Review Comments

**[user]** on `pymc/model/core.py`:

assert seems silly, given the `if name in self.coords` so close by. Maybe just a comment before the return?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
