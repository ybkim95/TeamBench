# Reference solution — GH879_pymc_8220

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH879_pymc_8220`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH879_pymc_8220/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `pymc/distributions/shape_utils.py` (modified, +1/-2)
- `tests/sampling/test_forward.py` (modified, +10/-0)

## Diff Summary (What the Fix Changes)

### `pymc/distributions/shape_utils.py`
```diff
@@ -309,8 +309,7 @@ def change_rv_size(op, rv, new_size, expand) -> TensorVariable:
     # to not unnecessarily pick up a `Cast` in some cases (see #4652).
     new_size = pt.as_tensor(new_size, ndim=1, dtype="int64")
 
-    new_rv = rv_node.op(*dist_params, size=new_size, dtype=rv.type.dtype)
-
+    new_rv = rv_node.op(*dist_params, size=new_size)
     # Replicate "traditional" rng default_update, if that was set for old_rng
     default_update = getattr(old_rng, "default_update", None)
     if default_update is not None:
```

## Moved from `brief.md`

## Files That May Need Changes

- `pymc/distributions/shape_utils.py`
