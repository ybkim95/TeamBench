# GH967_pymc_7844: Fix issues with model graph  — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pymc-devs/pymc/issues/7397
- Repo: https://github.com/pymc-devs/pymc

## Issue Description

I did just catch this bug: It comes from the `make_compute_graph` which causes a self loop

```python
from pymc.model_graph import ModelGraph

coords = {
    "obs": range(5),
}
with pm.Model(coords=coords) as model:
    data = pt.as_tensor_variable(
        np.ones((5, 3)),
        name="C",
    )
    pm.Deterministic("C", data, dims=("obs", None))

error_compute_graph = ModelGraph(model).make_compute_graph() # defaultdict(set, {"C": {"C"}})
# Visualize error:
pm.model_to_graphviz(model)
```
Result: 



![compute-graph-bug](https://github.com/pymc-devs/pymc/assets/57733339/39e3e38e-8e87-471f-8392-f04e02735345)

_Originally posted by [user] in https://github.com/pymc-devs/pymc/issues/7392#issuecomment-2196586849_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Take

## PR Review Comments

**[user]** on `tests/test_model_graph.py`:

You need to specify `obs` if you want it in the graph now. I don't see a reason to treat it differently from other Data variables?

**[user]** on `tests/test_model_graph.py`:

Agreed that it should always show by default. Very weird behavior otherwise?

**[user]** on `tests/test_model_graph.py`:

It's not that, when you specify a subset of variables it would show the observed data variables if you selected the observed variable,  but not say X data variables.

Now if you specify a subset it won't show it unless you specify it as well

**[user]** on `tests/test_model_graph.py`:

Oh, sure. If it's for user-specified subsets, you should get back what you ask for and nothing else.

**[user]** on `tests/test_model_graph.py`:

actually I think it should behave as before now .. should recheck it.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
