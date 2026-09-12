# Reference solution — GH995_scikit_learn_19490

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH995_scikit_learn_19490`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH995_scikit_learn_19490/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/whats_new/v1.1.rst` (modified, +9/-4)
- `sklearn/decomposition/_fastica.py` (modified, +79/-47)
- `sklearn/decomposition/tests/test_fastica.py` (modified, +113/-33)
- `sklearn/tests/test_docstring_parameters.py` (modified, +4/-0)

## Diff Summary (What the Fix Changes)

### `sklearn/decomposition/_fastica.py`
```diff
@@ -152,7 +152,7 @@ def fastica(
     n_components=None,
     *,
     algorithm="parallel",
-    whiten=True,
+    whiten="warn",
     fun="logcosh",
     fun_args=None,
     max_iter=200,
@@ -182,12 +182,18 @@ def fastica(
     algorithm : {'parallel', 'deflation'}, default='parallel'
         Apply a parallel or deflational FASTICA algorithm.
 
-    whiten : bool, default=True
-        If True perform an initial whitening of the data.
-        If False, the data is assumed to have already been
-        preprocessed: it should be centered, normed and white.
-        Otherwise you will get incorrect results.
-        In this case the parameter n_components will be ignored.
+    whiten : str or bool, default="warn"
+        Specify the whitening strategy to use.
+        If 'arbitrary-variance'  (default), a whitening with variance arbitrary is used.
+        If 'unit-variance', the whitening matrix is rescaled to ensure that each
+        recovered source has unit variance.
+        If False, the data is already considered to be whitened, and no
+        whitening is performed.
+
+        .. deprecated:: 1.1
+            From version 1.3, `whiten='unit-variance'` will be used by default.
+            `whiten=True` is deprecated from 1.1 and will raise ValueError in 1.3.
+            Use `whiten=arbitrary-variance` instead.
 
     fun : {'logcosh', 'exp', 'cube'} or callable, default='logcosh'
         The functional form of the G function used in the
@@ -280,7 +286,6 @@ def my_g(x):
            Algorithms and Applications, Neural Networks, 13(4-5), 2000,
            pp. 411-430.
     """
-
     est = FastICA(
         n_components=n_components,
         algorithm=algorithm,
@@ -292,31 +297,22 @@ def my_g(x):
         w_init=w_init,
         random_state=random_state,
     )
-    sources = est._fit(X, compute_sources=compute_sources)
-
-    if whiten:
-        if return_X_mean:
-            if return_n_iter:
-                return (est.whitening_, est._unmixing, sou
```

## Moved from `brief.md`

## Files That May Need Changes

- `sklearn/decomposition/_fastica.py`
