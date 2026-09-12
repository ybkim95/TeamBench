# Reference solution — GH1037_gpytorch_1685

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1037_gpytorch_1685`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1037_gpytorch_1685/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `gpytorch/kernels/kernel.py` (modified, +2/-2)
- `test/kernels/test_additive_and_product_kernels.py` (modified, +17/-0)

## Diff Summary (What the Fix Changes)

### `gpytorch/kernels/kernel.py`
```diff
@@ -331,8 +331,8 @@ def covar_dist(
         return res
 
     def named_sub_kernels(self):
-        for name, module in self._modules.items():
-            if isinstance(module, Kernel):
+        for name, module in self.named_modules():
+            if module is not self and isinstance(module, Kernel):
                 yield name, module
 
     def num_outputs_per_input(self, x1, x2):
```

## Moved from `brief.md`

## Files That May Need Changes

- `gpytorch/kernels/kernel.py`
