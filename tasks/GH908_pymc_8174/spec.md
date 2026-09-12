# GH908_pymc_8174: Fix broadcast check on log_jac_det — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pymc-devs/pymc/issues/8173
- Repo: https://github.com/pymc-devs/pymc

## Issue Description

### Describe the issue:

When freeze_dims_and_data is applied to a model containing a HalfStudentT RV with a size-1 dims coordinate, the subsequent `model.logp()` call raises a `ValueError`.

### Reproduceable code example:

```python
import pymc as pm
from pymc.model.transform.optimization import freeze_dims_and_data

with pm.Model(coords={'x_dim': ['only_one']}) as model:
    x = pm.HalfStudentT('x', nu=7, sigma=1, dims='x_dim')

fmodel = freeze_dims_and_data(model)
fmodel.logp()
```

### Error message:

```shell
Traceback (most recent call last):
  File "/home/velochy/salk/sandbox/debug/Rohetiiger3_elekter_clean_citizen_imputed_package/tmp_fa_test_pp_nps/test_st.py", line 8, in <module>
    fmodel.logp()  # raises ValueError
    ^^^^^^^^^^^^^
  File "/home/velochy/miniconda3/envs/salk/lib/python3.12/site-packages/pymc/model/core.py", line 711, in logp
    rv_logps = transformed_conditional_logp(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/velochy/miniconda3/envs/salk/lib/python3.12/site-packages/pymc/logprob/basic.py", line 642, in transformed_conditional_logp
    temp_logp_terms = conditional_logp(
                      ^^^^^^^^^^^^^^^^^
  File "/home/velochy/miniconda3/envs/salk/lib/python3.12/site-packages/pymc/logprob/basic.py", line 572, in conditional_logp
    node_logprobs = _logprob(
                    ^^^^^^^^^
  File "/home/velochy/miniconda3/envs/salk/lib/python3.12/functools.py", line 909, in wrapper
    return dispatch(args[0].__class__)(*args, **kw)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/velochy/miniconda3/envs/salk/lib/python3.12/site-packages/pymc/logprob/transform_value.py", line 116, in transformed_value_logprob
    raise ValueError(
ValueError: The logp of halfstudentt{inline=True} and log_jac_det of LogTransform are not allowed to broadcast together. There is a bug in the implementation of either one.
```

### PyMC version information:

PyMC 5.28.0
pytensor 2.38.1
Python 3.12

### Context for the issue:

After freezing, the size-1 dimension is replaced by a constant that PyTensor marks as broadcastable. This makes the logp of HalfStudentT return a tensor with broadcastable=(True,), while LogTransform.log_jac_det (computed from the forward value, not the frozen size) retains broadcastable=(False,). The mismatch triggers the validation check in transform_value.py.

The same pattern does not affect HalfNormal or Exponential (which use the same LogTransform), nor does it affect HalfStudentT with 2+ categories. It also does not occur on the unfrozen model — only after freeze_dims_and_data.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

It's an overly eager check. The right thing would be to add a `specify_broadcastable` on the `log_jac_det` if it's None. At runtime it must be 1, we just can't guarantee it is yet

### Comment 2 ([user]):

Will make the PR. This is on a rather common path for us, and while the workaround is to move to pm.Normal for the time being, it's not the greatest solution

### Comment 3 ([user]):

Ok, so turns out it goes even deeper, and can happen with generic pm.Normal.dist() too, meaning my planned workarounds would not work. 

Any chance you are planning a small bugfix release soon-ish and this can get included? Otherwise I'm likely stuck creating a pretty nasty temporary workaround

### Comment 4 ([user]):

Yes we can cut a patch

### Comment 5 ([user]):

Btw your immediate work-around should be simple, freeze the model immediately after defining the coords, and then build on the frozen model

### Comment 6 ([user]):

```python
import pymc as pm
from pymc.model.transform.optimization import freeze_dims_and_data

with freeze_dims_and_data(pm.Model(coords={'x_dim': ['only_one']})) as fmodel:
    x = pm.HalfStudentT('x', nu=7, sigma=1, dims='x_dim')

fmodel.logp()
```

### Comment 7 ([user]):

Or hack `fmodel._dim_lengths` to freeze just the one you need. You can see what it looks like before and after freezing.

### Comment 8 ([user]):

I don't think you quite appreciate the complexity of our modeling pipeline. The model construction and sampling is spread around over ~10 functions and the "freeze or not" is dependent on things that are generally determined after the model is put together. So yes, while in theory I could do what you say, in practice it would be about the complexity my other workaround plans would have been unfortunately :)

Somewhat awkward timing as we are about to have data come in on monday that actually needs this. But don't worry, I'll do the workaround if required. AI makes things pretty easy these days, especially if it's throwaway code like this will be.

### Comment 9 ([user]):

Sounds like you're pushing things to the extreme, nice. Your team should do a write up sometime (even if only to bash on the codebase)

### Comment 10 ([user]):

Yeah the things we do are regularly pushing me to the borders of my sanity trying to make sense of what exactly we are doing from the statistical perspective, and if it makes any sense or not. Basically, think Bambi, only we model multiple parallel linear models with different outcome models (some multinomial, some ordered probit/logit, some ordinal ranking like top3 or maxdiff)  at the same time, as we also want to model their inter-relations, and you'lll have a rough idea.

It's not even that proprietary per se. It's just, cleaning this up enough to share in a wider circle would be too much work, considering the amount of complexity it already allows. So there me and Erik are somewhat stuck trying to stay on top of it and keep it gradually improving, with two our two colleagues actively pushing the pipeline with every subsequent analysis. 

But I digress. I'll try to get the PR to the point you are happy to merge it, and then hope it will happen slightly sooner than later. Thank you for your quick response, as always [user] .

## PR Review Comments

**[user]** on `pymc/logprob/transform_value.py`:

comment is too verbose and specific

**[user]** on `pymc/logprob/transform_value.py`:

do we want to apply the specify both directions? If log_jac_det.type.shape==(None, 1) and log.shape.type.shape==(1, None), then both should have shape=(1, 1) to be valid?

The call can be wrapped in a try/except to raise the old more informative error in the case it is known to broadcast like (5, 1), vs (1, 5), which specify_broadcastable will raise immediately (IIRC)

**[user]** on `pymc/logprob/transform_value.py`:

My bad. AIs tend to be verbose with these...

**[user]** on `pymc/logprob/transform_value.py`:

Makes sense. Changed it to specify on both, and added the try-catch

**[user]** on `pymc/logprob/transform_value.py`:

can be simplified. 
`broadcastable_axes = [i for i, (ai, bi) in enumerate(zip(...)) if ai or bi]`

And then use in both.

There's no extra cost of specifying a broadcastable_axes that is already known to be broadcastable.

Only thing to make sure is that ndim matches

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
