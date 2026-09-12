# GH880_pymc_7877: Fix bug in mixture logprob inference with `None` indices — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pymc-devs/pymc/issues/7762
- Repo: https://github.com/pymc-devs/pymc

## Issue Description

### Describe the issue:

I just ran into a logprob rewrite error with an `AdvancedSubTensor` op that mixed `None` entries and `int32` indices together. This wasn't actually a mixture model but logprob found the op and tried to apply its rewrite rules and raised an error instead of just failing silently. The problem seems to be from [this line](https://github.com/pymc-devs/pymc/blob/main/pymc/logprob/mixture.py#L294) that doesn't include a guard against a `None` constant as well as a `slice` constant.

### Reproduceable code example:

```python
import numpy as np
import pymc as pm


obs = np.random.default_rng().normal(size=(7, 4))
with pm.Model():
   inds = np.arange(obs.shape[1])
   a = pm.Normal("a", shape=10)
   b = pm.Deterministic("b", a[None, inds])
   c = pm.Normal("c", mu=b, sigma=1, observed=obs)
   pm.sample()
```

### Error message:

```python
ERROR (pytensor.graph.rewriting.basic): Rewrite failure due to: find_measurable_index_mixture
ERROR (pytensor.graph.rewriting.basic): node: AdvancedSubtensor(a, NoneConst{None}, [0 1 2 3])
ERROR (pytensor.graph.rewriting.basic): TRACEBACK:
ERROR (pytensor.graph.rewriting.basic): Traceback (most recent call last):
  File "pytensor/graph/rewriting/basic.py", line 1913, in process_node
    replacements = node_rewriter.transform(fgraph, node)
  File "pytensor/graph/rewriting/basic.py", line 1085, in transform
    return self.fn(fgraph, node)
  File "pymc/logprob/mixture.py", line 291, in find_measurable_index_mixture
    if any(
  File "pymc/logprob/mixture.py", line 292, in <genexpr>
    indices.dtype.startswith("int") and sum(1 - b for b in indices.type.broadcastable) > 0
AttributeError: 'Constant' object has no attribute 'dtype'. Did you mean: 'type'?
```
but sampling works fine because the rewrite was actually supposed to fail and return `None`.

### PyMC version information:

Github main

### Context for the issue:

This doesn't really affect anything. It just confuses regular users that see the error traceback from rewriting and get alarmed. It would be more elegant to handle this extra indexer type just like with slice constants.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

hi [user] just to understand the end outcome, are we expecting it to skip the check if that is constant or none value? 

as in you case it is a constant and the condition that is trying to get dtype of it which it not possible here. 

Thanks

### Comment 2 ([user]):

Hi [user]. The [line that I quoted above](https://github.com/pymc-devs/pymc/blob/main/pymc/logprob/mixture.py#L294) needs to also check if the indices are `None` or [`NoneConst`](https://github.com/pymc-devs/pytensor/blob/main/pytensor/tensor/type_other.py#L132). That way, the rewrite will return `None` when it has a mixture of integer indexes, and slices **or new axis**.
If you look through the code base, you’ll see that rewrites have a bunch of conditions that check whether the rewrite could be applied to the inputs. When the conditions fail, the rewrite returns `None`. When it succeeds, it returns the modified graph or node. By adding the extra check on that condition, we are explicitly telling pytensor that the rewrite can’t work if the indexing operation mixes integers and other basic indexing things.

### Comment 3 ([user]):

Hi, I have raised a pr for the same, can you check that once. 

Thanks

### Comment 4 ([user]):

Hi [user] , [user] - I created a PR ( #7877 ) to address this issue. I used a `hasattr` guard, which might not be explicit enough, but it handles different conditions, `None`, `SliceConstant` etc. Please let me know on the PR if this is acceptable. 

I also addressed this [comment]((withheld: the upstream fix is not part of the task)files#r2136415944) about using `pytest.raises`. Thank you 🙏

## PR Review Comments

**[user]** on `pymc/logprob/mixture.py`:

You can check `isinstance(indices, TensorVariable)` and then it's guaranteed to have a dtype and a broadcastable

**[user]** on `pymc/logprob/mixture.py`:

While we are here, a bit more readable:
```suggestion
            and not all(indices.type.broadcastable)
```

**[user]** on `tests/logprob/test_mixture.py`:

Match on the error message to be more robust as a test

```suggestion
    with pytest.raises(RuntimeError, match=) as e:
```

**[user]** on `tests/logprob/test_mixture.py`:

I don't think we need this, if there was an AttributeError it would have raised, pytest only catches the specific error, even more with a match

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
