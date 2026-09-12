# Reference solution — GH953_scikit_learn_20853

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH953_scikit_learn_20853`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH953_scikit_learn_20853/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `sklearn/ensemble/_forest.py` (modified, +4/-2)
- `sklearn/linear_model/_ransac.py` (modified, +16/-7)
- `sklearn/multiclass.py` (modified, +7/-6)
- `sklearn/semi_supervised/_self_training.py` (modified, +35/-7)
- `sklearn/tests/test_common.py` (modified, +13/-5)
- `sklearn/tests/test_multiclass.py` (modified, +83/-8)

## Diff Summary (What the Fix Changes)

### `sklearn/ensemble/_forest.py`
```diff
@@ -565,8 +565,10 @@ def _validate_X_predict(self, X):
         """
         Validate X whenever one tries to predict, apply, predict_proba."""
         check_is_fitted(self)
-        self._check_feature_names(X, reset=False)
-        return self.estimators_[0]._validate_X_predict(X, check_input=True)
+        X = self._validate_data(X, dtype=DTYPE, accept_sparse="csr", reset=False)
+        if issparse(X) and (X.indices.dtype != np.intc or X.indptr.dtype != np.intc):
+            raise ValueError("No support for np.int64 index based sparse matrices")
+        return X
 
     @property
     def feature_importances_(self):
```

### `sklearn/linear_model/_ransac.py`
```diff
@@ -289,9 +289,10 @@ def fit(self, X, y, sample_weight=None):
             `max_trials` randomly chosen sub-samples.
 
         """
-        # Need to validate separately here.
-        # We can't pass multi_ouput=True because that would allow y to be csr.
-        check_X_params = dict(accept_sparse="csr")
+        # Need to validate separately here. We can't pass multi_ouput=True
+        # because that would allow y to be csr. Delay expensive finiteness
+        # check to the base estimator's own input validation.
+        check_X_params = dict(accept_sparse="csr", force_all_finite=False)
         check_y_params = dict(ensure_2d=False)
         X, y = self._validate_data(
             X, y, validate_separately=(check_X_params, check_y_params)
@@ -562,8 +563,12 @@ def predict(self, X):
             Returns predicted values.
         """
         check_is_fitted(self)
-        self._check_feature_names(X, reset=False)
-
+        X = self._validate_data(
+            X,
+            force_all_finite=False,
+            accept_sparse=True,
+            reset=False,
+        )
         return self.estimator_.predict(X)
 
     def score(self, X, y):
@@ -585,8 +590,12 @@ def score(self, X, y):
             Score of the prediction.
         """
         check_is_fitted(self)
-        self._check_feature_names(X, reset=False)
-
+        X = self._validate_data(
+            X,
+            force_all_finite=False,
+            accept_sparse=True,
+            reset=False,
+        )
         return self.estimator_.score(X, y)
 
     def _more_tags(self):
```

### `sklearn/multiclass.py`
```diff
@@ -667,8 +667,7 @@ class OneVsOneClassifier(MetaEstimatorMixin, ClassifierMixin, BaseEstimator):
             pairwise estimator tag instead.
 
     n_features_in_ : int
-        Number of features seen during :term:`fit`. Only defined if the
-        underlying estimator exposes such an attribute when fit.
+        Number of features seen during :term:`fit`.
 
         .. versionadded:: 0.24
 
@@ -740,9 +739,6 @@ def fit(self, X, y):
 
         self.estimators_ = estimators_indices[0]
 
-        if hasattr(self.estimators_[0], "n_features_in_"):
-            self.n_features_in_ = self.estimators_[0].n_features_in_
-
         pairwise = _is_pairwise(self)
         self.pairwise_indices_ = estimators_indices[1] if pairwise else None
 
@@ -857,7 +853,12 @@ def decision_function(self, X):
                 scikit-learn conventions for binary classification.
         """
         check_is_fitted(self)
-        self._check_feature_names(X, reset=False)
+        X = self._validate_data(
+            X,
+            accept_sparse=True,
+            force_all_finite=False,
+            reset=False,
+        )
 
         indices = self.pairwise_indices_
         if indices is None:
```

### `sklearn/semi_supervised/_self_training.py`
```diff
@@ -169,8 +169,11 @@ def fit(self, X, y):
         self : object
             Returns an instance of self.
         """
-        # we need row slicing support for sparce matrices
-        X, y = self._validate_data(X, y, accept_sparse=["csr", "csc", "lil", "dok"])
+        # we need row slicing support for sparce matrices, but costly finiteness check
+        # can be delegated to the base estimator.
+        X, y = self._validate_data(
+            X, y, accept_sparse=["csr", "csc", "lil", "dok"], force_all_finite=False
+        )
 
         if self.base_estimator is None:
             raise ValueError("base_estimator cannot be None!")
@@ -291,7 +294,12 @@ def predict(self, X):
             Array with predicted labels.
         """
         check_is_fitted(self)
-        self._check_feature_names(X, reset=False)
+        X = self._validate_data(
+            X,
+            accept_sparse=True,
+            force_all_finite=False,
+            reset=False,
+        )
         return self.base_estimator_.predict(X)
 
     def predict_proba(self, X):
@@ -308,7 +316,12 @@ def predict_proba(self, X):
             Array with prediction probabilities.
         """
         check_is_fitted(self)
-        self._check_feature_names(X, reset=False)
+        X = self._validate_data(
+            X,
+            accept_sparse=True,
+            force_all_finite=False,
+            reset=False,
+        )
         return self.base_estimator_.predict_proba(X)
 
     @if_delegate_has_method(delegate="base_estimator")
@@ -326,7 +339,12 @@ def decision_function(self, X):
             Result of the decision function of the `base_estimator`.
         """
         check_is_fitted(self)
-        self._check_feature_names(X, reset=False)
+        X = self._validate_data(
+            X,
+            accept_sparse=True,
+            force_all_finite=False,
+            reset=False,
+        )
         return self.base_estimator_.decision_function(X)
 
     @if_delegate_has_method(delegate
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `sklearn/ensemble/_forest.py`
- `sklearn/linear_model/_ransac.py`
- `sklearn/multiclass.py`
- `sklearn/semi_supervised/_self_training.py`
