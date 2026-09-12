# Reference solution — GH957_scipy_20272

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH957_scipy_20272`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH957_scipy_20272/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `scipy/optimize/_trustregion_exact.py` (modified, +1/-0)
- `scipy/optimize/tests/test_trustregion_exact.py` (modified, +14/-1)

## Diff Summary (What the Fix Changes)

### `scipy/optimize/_trustregion_exact.py`
```diff
@@ -386,6 +386,7 @@ def solve(self, tr_radius):
                         # Update damping factor
                         lambda_current = lambda_new
                         already_factorized = True
+                        U = c
                     else:  # Unsuccessful factorization
                         # Update uncertainty bounds
                         lambda_lb = max(lambda_lb, lambda_new)
```

## Moved from `brief.md`

## Files That May Need Changes

- `scipy/optimize/_trustregion_exact.py`
