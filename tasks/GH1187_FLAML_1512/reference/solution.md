# Reference solution — GH1187_FLAML_1512

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1187_FLAML_1512`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1187_FLAML_1512/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `.github/copilot-instructions.md` (modified, +1/-0)
- `flaml/automl/model.py` (modified, +26/-0)
- `test/automl/test_sklearn_17_compat.py` (added, +89/-0)

## Diff Summary (What the Fix Changes)

### `flaml/automl/model.py`
```diff
@@ -26,6 +26,13 @@
 from sklearn.svm import LinearSVC
 from xgboost import __version__ as xgboost_version
 
+try:
+    from sklearn.utils._tags import ClassifierTags, RegressorTags
+
+    SKLEARN_TAGS_AVAILABLE = True
+except ImportError:
+    SKLEARN_TAGS_AVAILABLE = False
+
 from flaml import tune
 from flaml.automl.data import group_counts
 from flaml.automl.spark import ERROR as SPARK_ERROR
@@ -148,6 +155,25 @@ def get_params(self, deep=False):
             params["_estimator_type"] = self._estimator_type
         return params
 
+    def __sklearn_tags__(self):
+        """Override sklearn tags to respect the _estimator_type attribute.
+
+        This is needed for sklearn 1.7+ which uses get_tags() instead of
+        checking _estimator_type directly. Since BaseEstimator inherits from
+        ClassifierMixin, it would otherwise always be tagged as a classifier.
+        """
+        tags = super().__sklearn_tags__()
+        if hasattr(self, "_estimator_type") and SKLEARN_TAGS_AVAILABLE:
+            if self._estimator_type == "regressor":
+                tags.estimator_type = "regressor"
+                tags.regressor_tags = RegressorTags()
+                tags.classifier_tags = None
+            elif self._estimator_type == "classifier":
+                tags.estimator_type = "classifier"
+                tags.classifier_tags = ClassifierTags()
+                tags.regressor_tags = None
+        return tags
+
     @property
     def classes_(self):
         return self._model.classes_
```

## Moved from `brief.md`

## Files That May Need Changes

- `flaml/automl/model.py`
