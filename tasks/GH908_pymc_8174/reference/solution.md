# Reference solution — GH908_pymc_8174

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH908_pymc_8174`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH908_pymc_8174/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `pymc/logprob/transform_value.py` (modified, +13/-4)
- `tests/distributions/test_transform.py` (modified, +7/-7)
- `tests/logprob/test_transform_value.py` (modified, +14/-0)

## Diff Summary (What the Fix Changes)

### `pymc/logprob/transform_value.py`
```diff
@@ -16,6 +16,7 @@
 from collections.abc import Sequence
 
 import numpy as np
+import pytensor.tensor as pt
 
 from pytensor.graph import Apply, Op
 from pytensor.graph.features import AlreadyThere, Feature
@@ -113,10 +114,18 @@ def transformed_value_logprob(op, values, *rv_outs, use_jacobian=True, **kwargs)
             )
         # Check there is no broadcasting between logp and jacobian
         if logp.type.broadcastable != log_jac_det.type.broadcastable:
-            raise ValueError(
-                f"The logp of {rv_op} and log_jac_det of {transform} are not allowed to broadcast together. "
-                "There is a bug in the implementation of either one."
-            )
+            lb, jb = logp.type.broadcastable, log_jac_det.type.broadcastable
+            broadcastable_axes = [
+                i for i, (ai, bi) in enumerate(zip(lb, jb, strict=True)) if ai or bi
+            ]
+            try:
+                logp = pt.specify_broadcastable(logp, *broadcastable_axes)
+                log_jac_det = pt.specify_broadcastable(log_jac_det, *broadcastable_axes)
+            except ValueError as err:
+                raise ValueError(
+                    f"The logp of {rv_op} and log_jac_det of {transform} are not allowed to broadcast together. "
+                    "There is a bug in the implementation of either one."
+                ) from err
 
         if use_jacobian:
             if value.name:
```

## Moved from `brief.md`

## Files That May Need Changes

- `pymc/logprob/transform_value.py`
