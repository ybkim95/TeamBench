# Reference solution — GH901_scikit_learn_19085

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH901_scikit_learn_19085`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH901_scikit_learn_19085/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/whats_new/v1.1.rst` (modified, +3/-0)
- `sklearn/metrics/_ranking.py` (modified, +14/-4)
- `sklearn/metrics/tests/test_ranking.py` (modified, +60/-23)

## Diff Summary (What the Fix Changes)

### `sklearn/metrics/_ranking.py`
```diff
@@ -865,15 +865,25 @@ def precision_recall_curve(y_true, probas_pred, *, pos_label=None, sample_weight
         y_true, probas_pred, pos_label=pos_label, sample_weight=sample_weight
     )
 
-    precision = tps / (tps + fps)
-    precision[np.isnan(precision)] = 0
-    recall = tps / tps[-1]
+    ps = tps + fps
+    precision = np.divide(tps, ps, where=(ps != 0))
+
+    # When no positive label in y_true, recall is set to 1 for all thresholds
+    # tps[-1] == 0 <=> y_true == all negative labels
+    if tps[-1] == 0:
+        warnings.warn(
+            "No positive class found in y_true, "
+            "recall is set to one for all thresholds."
+        )
+        recall = np.ones_like(tps)
+    else:
+        recall = tps / tps[-1]
 
     # stop when full recall attained
     # and reverse the outputs so recall is decreasing
     last_ind = tps.searchsorted(tps[-1])
     sl = slice(last_ind, None, -1)
-    return np.r_[precision[sl], 1], np.r_[recall[sl], 0], thresholds[sl]
+    return np.hstack((precision[sl], 1)), np.hstack((recall[sl], 0)), thresholds[sl]
 
 
 def roc_curve(
```

## Moved from `brief.md`

## Files That May Need Changes

- `sklearn/metrics/_ranking.py`
