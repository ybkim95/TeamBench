# Reference solution — GH888_pytorch_lightni_20872

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH888_pytorch_lightni_20872`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH888_pytorch_lightni_20872/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/lightning/fabric/CHANGELOG.md` (modified, +6/-0)
- `src/lightning/fabric/plugins/environments/xla.py` (modified, +15/-0)
- `tests/tests_fabric/plugins/environments/test_xla.py` (modified, +61/-0)

## Diff Summary (What the Fix Changes)

### `src/lightning/fabric/plugins/environments/xla.py`
```diff
@@ -66,6 +66,11 @@ def world_size(self) -> int:
         The output is cached for performance.
 
         """
+        if _XLA_GREATER_EQUAL_2_1:
+            from torch_xla import runtime as xr
+
+            return xr.world_size()
+
         import torch_xla.core.xla_model as xm
 
         return xm.xrt_world_size()
@@ -82,6 +87,11 @@ def global_rank(self) -> int:
         The output is cached for performance.
 
         """
+        if _XLA_GREATER_EQUAL_2_1:
+            from torch_xla import runtime as xr
+
+            return xr.global_ordinal()
+
         import torch_xla.core.xla_model as xm
 
         return xm.get_ordinal()
@@ -98,6 +108,11 @@ def local_rank(self) -> int:
         The output is cached for performance.
 
         """
+        if _XLA_GREATER_EQUAL_2_1:
+            from torch_xla import runtime as xr
+
+            return xr.local_ordinal()
+
         import torch_xla.core.xla_model as xm
 
         return xm.get_local_ordinal()
```

## Moved from `brief.md`

## Files That May Need Changes

- `src/lightning/fabric/plugins/environments/xla.py`
