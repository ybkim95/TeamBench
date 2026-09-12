# Reference solution — GH975_scikit_learn_29612

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH975_scikit_learn_29612`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH975_scikit_learn_29612/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/whats_new/v1.6.rst` (modified, +8/-0)
- `sklearn/decomposition/_fastica.py` (modified, +1/-1)
- `sklearn/decomposition/tests/test_fastica.py` (modified, +7/-2)

## Diff Summary (What the Fix Changes)

### `sklearn/decomposition/_fastica.py`
```diff
@@ -605,7 +605,7 @@ def g(x, fun_args):
                 # Faster when num_samples >> n_features
                 d, u = linalg.eigh(XT.dot(X))
                 sort_indices = np.argsort(d)[::-1]
-                eps = np.finfo(d.dtype).eps
+                eps = np.finfo(d.dtype).eps * 10
                 degenerate_idx = d < eps
                 if np.any(degenerate_idx):
                     warnings.warn(
```

## Moved from `brief.md`

## Files That May Need Changes

- `sklearn/decomposition/_fastica.py`
