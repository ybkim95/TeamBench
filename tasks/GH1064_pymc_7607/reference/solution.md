# Reference solution — GH1064_pymc_7607

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1064_pymc_7607`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1064_pymc_7607/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `conda-envs/environment-dev.yml` (modified, +1/-1)
- `conda-envs/environment-docs.yml` (modified, +1/-1)
- `conda-envs/environment-jax.yml` (modified, +1/-1)
- `conda-envs/environment-test.yml` (modified, +1/-1)
- `conda-envs/windows-environment-dev.yml` (modified, +1/-1)
- `conda-envs/windows-environment-test.yml` (modified, +1/-1)
- `pymc/sampling/mcmc.py` (modified, +12/-4)
- `requirements-dev.txt` (modified, +1/-1)
- `requirements.txt` (modified, +1/-1)
- `tests/distributions/test_custom.py` (modified, +1/-1)

## Diff Summary (What the Fix Changes)

### `pymc/sampling/mcmc.py`
```diff
@@ -528,10 +528,8 @@ def sample(
     random_seed : int, array-like of int, or Generator, optional
         Random seed(s) used by the sampling steps. Each step will create its own
         :py:class:`~numpy.random.Generator` object to make its random draws in a way that is
-        indepedent from all other steppers and all other chains. If a list, tuple or array of ints
-        is passed, each entry will be used to seed the creation of ``Generator`` objects.
-        A ``ValueError`` will be raised if the length does not match the number of chains.
-        A ``TypeError`` will be raised if a :py:class:`~numpy.random.RandomState` object is passed.
+        indepedent from all other steppers and all other chains.
+        A ``TypeError`` will be raised if a legacy :py:class:`~numpy.random.RandomState` object is passed.
         We no longer support ``RandomState`` objects because their seeding mechanism does not allow
         easy spawning of new independent random streams that are needed by the step methods.
     progressbar : bool, optional default=True
@@ -729,7 +727,17 @@ def joined_blas_limiter():
         )
 
     if random_seed == -1:
+        warnings.warn(
+            "Setting random_seed = -1 is deprecated. Pass `None` to not specify a seed.",
+            FutureWarning,
+        )
         random_seed = None
+    elif isinstance(random_seed, tuple | list):
+        warnings.warn(
+            "A list or tuple of random_seed no longer specifies the specific random_seed of each chain. "
+            "Use a single seed instead.",
+            UserWarning,
+        )
     rngs = get_random_generator(random_seed).spawn(chains)
     random_seed_list = [rng.integers(2**30) for rng in rngs]
 
```

## Moved from `brief.md`

## Files That May Need Changes

- `pymc/sampling/mcmc.py`
