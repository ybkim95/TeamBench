# Reference solution — GH945_autogluon_3294

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH945_autogluon_3294`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH945_autogluon_3294/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `core/src/autogluon/core/utils/utils.py` (modified, +7/-2)
- `tabular/src/autogluon/tabular/learner/abstract_learner.py` (modified, +72/-52)
- `tabular/tests/unittests/test_tabular.py` (modified, +35/-14)

## Diff Summary (What the Fix Changes)

### `core/src/autogluon/core/utils/utils.py`
```diff
@@ -264,12 +264,17 @@ def get_pred_from_proba_df(y_pred_proba, problem_type=BINARY):
     return y_pred
 
 
-def get_pred_from_proba(y_pred_proba, problem_type=BINARY):
+def get_pred_from_proba(y_pred_proba: np.ndarray, problem_type=BINARY):
     if problem_type == BINARY:
         # Using > instead of >= to align with Pandas `.idxmax` logic which picks the left-most column during ties.
         # If this is not done, then predictions can be inconsistent when converting in binary classification from multiclass-form pred_proba and
         # binary-form pred_proba when the pred_proba is 0.5 for positive and negative classes.
-        y_pred = [1 if pred > 0.5 else 0 for pred in y_pred_proba]
+        if len(y_pred_proba.shape) == 2:
+            assert y_pred_proba.shape[1] == 2
+            # Assume positive class is in 2nd position
+            y_pred = [1 if pred > 0.5 else 0 for pred in y_pred_proba[:, 1]]
+        else:
+            y_pred = [1 if pred > 0.5 else 0 for pred in y_pred_proba]
     elif problem_type == REGRESSION:
         y_pred = y_pred_proba
     elif problem_type == QUANTILE:
```

### `tabular/src/autogluon/tabular/learner/abstract_learner.py`
```diff
@@ -98,6 +98,10 @@ def feature_generators(self):
     def class_labels(self):
         return self.label_cleaner.ordered_class_labels
 
+    @property
+    def class_labels_transformed(self):
+        return self.label_cleaner.ordered_class_labels_transformed
+
     @property
     def positive_class(self):
         """
@@ -129,66 +133,75 @@ def _fit(self, X: DataFrame, X_val: DataFrame = None, scheduler_options=None, hy
         raise NotImplementedError
 
     def predict_proba(self, X: DataFrame, model=None, as_pandas=True, as_multiclass=True, inverse_transform=True, transform_features=True):
-        if as_pandas:
-            X_index = copy.deepcopy(X.index)
-        else:
-            X_index = None
+        X_index = copy.deepcopy(X.index) if as_pandas else None
         if X.empty:
             y_pred_proba = np.array([])
         else:
             if transform_features:
                 X = self.transform_features(X)
             y_pred_proba = self.load_trainer().predict_proba(X, model=model)
-        if inverse_transform:
-            y_pred_proba = self.label_cleaner.inverse_transform_proba(y_pred_proba)
-        if as_multiclass and (self.problem_type == BINARY):
-            y_pred_proba = LabelCleanerMulticlassToBinary.convert_binary_proba_to_multiclass_proba(y_pred_proba)
-        if as_pandas:
-            if self.problem_type == MULTICLASS or (as_multiclass and self.problem_type == BINARY):
-                y_pred_proba = pd.DataFrame(data=y_pred_proba, columns=self.class_labels, index=X_index)
-            elif self.problem_type == QUANTILE:
-                y_pred_proba = pd.DataFrame(data=y_pred_proba, columns=self.quantile_levels, index=X_index)
-            else:
-                y_pred_proba = pd.Series(data=y_pred_proba, name=self.label, index=X_index)
+        y_pred_proba = self._post_process_predict_proba(y_pred_proba=y_pred_proba,
+                                                        as_pandas=as_pandas,
+                             
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `core/src/autogluon/core/utils/utils.py`
- `tabular/src/autogluon/tabular/learner/abstract_learner.py`
