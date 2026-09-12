# Reference solution — GH1087_scikit_learn_30373

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1087_scikit_learn_30373`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1087_scikit_learn_30373/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `sklearn/ensemble/_forest.py` (modified, +0/-5)
- `sklearn/utils/_tags.py` (modified, +11/-11)
- `sklearn/utils/estimator_checks.py` (modified, +0/-1)
- `sklearn/utils/tests/test_tags.py` (modified, +1/-2)

## Diff Summary (What the Fix Changes)

### `sklearn/ensemble/_forest.py`
```diff
@@ -1165,11 +1165,6 @@ def _compute_partial_dependence_recursion(self, grid, target_features):
 
         return averaged_predictions
 
-    def __sklearn_tags__(self):
-        tags = super().__sklearn_tags__()
-        tags.regressor_tags.multi_label = True
-        return tags
-
 
 class RandomForestClassifier(ForestClassifier):
     """
```

### `sklearn/utils/_tags.py`
```diff
@@ -98,6 +98,8 @@ class TargetTags:
         Whether a regressor supports multi-target outputs or a classifier supports
         multi-class multi-output.
 
+        See :term:`multi-output` in the glossary.
+
     single_output : bool, default=True
         Whether the target can be single-output. This can be ``False`` if the
         estimator supports only multi-output cases.
@@ -150,8 +152,13 @@ class ClassifierTags:
         classification. Therefore this flag indicates whether the
         classifier is a binary-classifier-only or not.
 
+        See :term:`multi-class` in the glossary.
+
     multi_label : bool, default=False
-        Whether the classifier supports multi-label output.
+        Whether the classifier supports multi-label output: a data point can
+        be predicted to belong to a variable number of classes.
+
+        See :term:`multi-label` in the glossary.
     """
 
     poor_score: bool = False
@@ -172,13 +179,9 @@ class RegressorTags:
         n_informative=1, bias=5.0, noise=20, random_state=42)``. The
         dataset and values are based on current estimators in scikit-learn
         and might be replaced by something more systematic.
-
-    multi_label : bool, default=False
-        Whether the regressor supports multilabel output.
     """
 
     poor_score: bool = False
-    multi_label: bool = False
 
 
 @dataclass(**_dataclass_args())
@@ -496,7 +499,6 @@ def _to_new_tags(old_tags, estimator=None):
     if estimator_type == "regressor":
         regressor_tags = RegressorTags(
             poor_score=old_tags["poor_score"],
-            multi_label=old_tags["multilabel"],
         )
     else:
         regressor_tags = None
@@ -520,18 +522,16 @@ def _to_old_tags(new_tags):
     """Utility function convert old tags (dictionary) to new tags (dataclass)."""
     if new_tags.classifier_tags:
         binary_only = not new_tags.classifier_tags.multi_class
-        multilabel_clf = new_tags.classifier_tags.multi_label
+        multila
```

### `sklearn/utils/estimator_checks.py`
```diff
@@ -4438,7 +4438,6 @@ def check_valid_tag_types(name, estimator):
 
     if tags.regressor_tags is not None:
         assert isinstance(tags.regressor_tags.poor_score, bool), err_msg
-        assert isinstance(tags.regressor_tags.multi_label, bool), err_msg
 
     if tags.transformer_tags is not None:
         assert isinstance(tags.transformer_tags.preserves_dtype, list), err_msg
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `sklearn/ensemble/_forest.py`
- `sklearn/utils/_tags.py`
- `sklearn/utils/estimator_checks.py`
