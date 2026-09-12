# Reference solution — GH880_pymc_7877

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH880_pymc_7877`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH880_pymc_7877/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `pymc/logprob/mixture.py` (modified, +4/-3)
- `tests/logprob/test_mixture.py` (modified, +27/-0)

## Diff Summary (What the Fix Changes)

### `pymc/logprob/mixture.py`
```diff
@@ -62,7 +62,7 @@
     is_basic_idx,
 )
 from pytensor.tensor.type import TensorType
-from pytensor.tensor.type_other import NoneConst, NoneTypeT, SliceConstant, SliceType
+from pytensor.tensor.type_other import NoneConst, NoneTypeT, SliceType
 from pytensor.tensor.variable import TensorVariable
 
 from pymc.logprob.abstract import (
@@ -289,9 +289,10 @@ def find_measurable_index_mixture(fgraph, node):
         # We don't support (non-scalar) integer array indexing as it can pick repeated values,
         # but the Mixture logprob assumes all mixture values are independent
         if any(
-            indices.dtype.startswith("int") and sum(1 - b for b in indices.type.broadcastable) > 0
+            isinstance(indices, TensorVariable)
+            and indices.dtype.startswith("int")
+            and not all(indices.type.broadcastable)
             for indices in mixing_indices
-            if not isinstance(indices, SliceConstant)
         ):
             return None
 
```

## Moved from `brief.md`

## Files That May Need Changes

- `pymc/logprob/mixture.py`
