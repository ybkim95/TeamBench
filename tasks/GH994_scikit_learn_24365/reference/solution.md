# Reference solution — GH994_scikit_learn_24365

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH994_scikit_learn_24365`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH994_scikit_learn_24365/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/whats_new/v1.2.rst` (modified, +5/-0)
- `sklearn/metrics/_classification.py` (modified, +4/-2)
- `sklearn/metrics/tests/test_classification.py` (modified, +12/-1)

## Diff Summary (What the Fix Changes)

### `sklearn/metrics/_classification.py`
```diff
@@ -28,6 +28,7 @@
 
 from scipy.sparse import coo_matrix
 from scipy.sparse import csr_matrix
+from scipy.special import xlogy
 
 from ..preprocessing import LabelBinarizer
 from ..preprocessing import LabelEncoder
@@ -2629,8 +2630,9 @@ def log_loss(
             )
 
     # Renormalize
-    y_pred /= y_pred.sum(axis=1)[:, np.newaxis]
-    loss = -(transformed_labels * np.log(y_pred)).sum(axis=1)
+    y_pred_sum = y_pred.sum(axis=1)
+    y_pred = y_pred / y_pred_sum[:, np.newaxis]
+    loss = -xlogy(transformed_labels, y_pred).sum(axis=1)
 
     return _weighted_sum(loss, sample_weight, normalize)
 
```

## Moved from `brief.md`

## Files That May Need Changes

- `sklearn/metrics/_classification.py`
