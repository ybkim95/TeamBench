# GH1064_pymc_7607: Bump numpy version due to use of `Generator.spawn` only available in `>=1.25` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pymc-devs/pymc/issues/7605
- Repo: https://github.com/pymc-devs/pymc

## Issue Description

### Describe the issue:

PyMC now relies on the `spawn()` method from `numpy.random._generator.Generator`. But this is a relatively recent addition to numpy ([added in v1.25](https://numpy.org/doc/2.0/reference/random/generated/numpy.random.Generator.spawn.html)). So we need to set a lower limit on the numpy dependency.

### Reproduceable code example:

```python
import pymc as pm

with pm.Model() as model:
    a = pm.Normal("a")
    obs = pm.Normal("obs", a, 1, observed=[1,2])
    idata = pm.sample()
```


### Error message:


<details>
```shell
---------------------------------------------------------------------------
AttributeError                            Traceback (most recent call last)
Input In [7], in <cell line: 6>()
      7     a = pm.Normal("a")
      8     obs = pm.Normal("obs", a, 1, observed=[1,2])
----> 9     idata = pm.sample()
     11 print(az.summary(idata))
File ~/mambaforge/envs/pymc/lib/python3.10/site-packages/pymc/sampling/mcmc.py:733, in sample(draws, tune, chains, cores, random
_seed, progressbar, progressbar_theme, step, var_names, nuts_sampler, initvals, init, jitter_max_retries, n_init, trace, discard
_tuned_samples, compute_convergence_checks, keep_warning_stat, return_inferencedata, idata_kwargs, nuts_sampler_kwargs, callback
, mp_ctx, blas_cores, model, compile_kwargs, **kwargs)
    731 if random_seed == -1:
    732     random_seed = None
--> 733 rngs = get_random_generator(random_seed).spawn(chains)
    734 random_seed_list = [rng.integers(2**30) for rng in rngs]
    736 if not discard_tuned_samples and not return_inferencedata:
AttributeError: 'numpy.random._generator.Generator' object has no attribute 'spawn'
```
</details>


### PyMC version information:

<details>
# packages in environment at /home/xian/mambaforge/envs/pymc:
#
# Name                    Version                   Build  Channel
numpy                     1.24.2          py310h8deb116_0    conda-forge
pymc                      5.19.0               hd8ed1ab_0    conda-forge
pymc-base                 5.19.0             pyhd8ed1ab_0    conda-forge
pytensor                  2.26.4          py310ha549d7f_0    conda-forge
pytensor-base             2.26.4          py310h89e8f5a_0    conda-forge
</details>

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

This was true as of 5.18, I ran into the problem last week and didn't think to file a report sorry! From this commit: (withheld: the upstream fix is not part of the task)

## PR Review Comments

**[user]** on `pymc/step_methods/hmc/base_hmc.py`:

Why was this spawning a new rng?

**[user]** on `pymc/sampling/mcmc.py`:

This needs to change a bit. `np.random.SeedSequence` will create a new `SeedSequence`, not a `Generator`. I suppose that you can access the generator's seed sequence as `get_random_generator(random_seed).bit_generator.seed_seq`, and then `spawn` from there.

From the numpy source, it looks rather easy to be able to [spawn new `Generator`s](https://github.com/numpy/numpy/blob/main/numpy/random/_generator.pyx#L301) from `BitGenerator`s. But the spawn method for those was also added on version 1.25, so we'll have to also look at how [`BitGenerator.spawn`](https://github.com/numpy/numpy/blob/main/numpy/random/bit_generator.pyx#L632) works off of seed sequences.

I think that the way to go would look something like:

```python
bit_gen = rng.bit_generator
seed_seq = bit_gen.seed_seq
rngs = [type(rng)(type(bit_gen)(seed)) for seed in seed_seq.spawn(chains)]
```

**[user]** on `pymc/sampling/mcmc.py`:

This could be unpacked into a utility function and used on the other similar calls

**[user]** on `pymc/sampling/mcmc.py`:

I see, so maybe lets just bumpy numpy min version?

**[user]** on `pymc/sampling/mcmc.py`:

Okay numpy is dropping support for 1.24 on december 18, so maybe it's just fine: https://numpy.org/neps/nep-0029-deprecation_policy.html#drop-schedule

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
