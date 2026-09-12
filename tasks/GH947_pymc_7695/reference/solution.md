# Reference solution — GH947_pymc_7695

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH947_pymc_7695`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH947_pymc_7695/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `pymc/sampling/jax.py` (modified, +4/-1)
- `tests/sampling/test_jax.py` (modified, +21/-0)

## Diff Summary (What the Fix Changes)

### `pymc/sampling/jax.py`
```diff
@@ -240,7 +240,10 @@ def eval_logp_initial_point(point: dict[str, np.ndarray]) -> jax.Array:
             Wraps jaxified logp function to accept a dict of
             {model_variable: np.array} key:value pairs.
             """
-            return logp_fn(point.values())
+            # Because logp_fn is not jitted, we need to convert inputs to jax arrays,
+            # or some methods that are only available for jax arrays will fail
+            # such as x.at[indices].set(y)
+            return logp_fn([jax.numpy.asarray(v) for v in point.values()])
 
     initial_points = _init_jitter(
         model,
```

## Moved from `brief.md`

## Files That May Need Changes

- `pymc/sampling/jax.py`
