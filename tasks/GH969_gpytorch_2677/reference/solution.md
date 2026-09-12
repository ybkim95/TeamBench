# Reference solution — GH969_gpytorch_2677

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH969_gpytorch_2677`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH969_gpytorch_2677/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `gpytorch/kernels/rq_kernel.py` (modified, +8/-3)
- `test/kernels/test_rq_kernel.py` (modified, +31/-0)

## Diff Summary (What the Fix Changes)

### `gpytorch/kernels/rq_kernel.py`
```diff
@@ -60,17 +60,22 @@ def __init__(self, alpha_constraint: Optional[Interval] = None, **kwargs):
 
         self.register_constraint("raw_alpha", alpha_constraint)
 
-    def forward(self, x1, x2, diag=False, **params):
+    def forward(self, x1, x2, diag=False, last_dim_is_batch=False, **params):
         def postprocess_rq(dist_mat):
             alpha = self.alpha
-            for _ in range(1, len(dist_mat.shape) - len(self.batch_shape)):
+
+            if not diag:
+                alpha = alpha.unsqueeze(-1)
+
+            if last_dim_is_batch:
                 alpha = alpha.unsqueeze(-1)
+
             return (1 + dist_mat.div(2 * alpha)).pow(-alpha)
 
         x1_ = x1.div(self.lengthscale)
         x2_ = x2.div(self.lengthscale)
         return postprocess_rq(
-            self.covar_dist(x1_, x2_, square_dist=True, diag=diag, **params),
+            self.covar_dist(x1_, x2_, square_dist=True, diag=diag, last_dim_is_batch=last_dim_is_batch, **params),
         )
 
     @property
```

## Moved from `brief.md`

## Files That May Need Changes

- `gpytorch/kernels/rq_kernel.py`
