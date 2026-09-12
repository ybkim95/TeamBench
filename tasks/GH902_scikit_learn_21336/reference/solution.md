# Reference solution — GH902_scikit_learn_21336

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH902_scikit_learn_21336`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH902_scikit_learn_21336/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/whats_new/v1.0.rst` (modified, +9/-0)
- `sklearn/svm/_base.py` (modified, +7/-0)
- `sklearn/svm/tests/test_svm.py` (modified, +13/-0)

## Diff Summary (What the Fix Changes)

### `sklearn/svm/_base.py`
```diff
@@ -616,6 +616,13 @@ def _validate_for_predict(self, X):
                     "the number of samples at training time"
                     % (X.shape[1], self.shape_fit_[0])
                 )
+        # Fixes https://nvd.nist.gov/vuln/detail/CVE-2020-28975
+        # Check that _n_support is consistent with support_vectors
+        sv = self.support_vectors_
+        if not self._sparse and sv.size > 0 and self.n_support_.sum() != sv.shape[0]:
+            raise ValueError(
+                f"The internal representation of {self.__class__.__name__} was altered"
+            )
         return X
 
     @property
```

## Moved from `brief.md`

## Files That May Need Changes

- `sklearn/svm/_base.py`
