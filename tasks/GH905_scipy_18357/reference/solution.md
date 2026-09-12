# Reference solution — GH905_scipy_18357

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH905_scipy_18357`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH905_scipy_18357/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `scipy/sparse/linalg/_interface.py` (modified, +29/-8)
- `scipy/sparse/linalg/tests/test_interface.py` (modified, +13/-0)

## Diff Summary (What the Fix Changes)

### `scipy/sparse/linalg/_interface.py`
```diff
@@ -325,8 +325,8 @@ def matmat(self, X):
         _matmat method to ensure that y has the correct type.
 
         """
-
-        X = np.asanyarray(X)
+        if not (isspmatrix(X) or is_pydata_spmatrix(X)):
+            X = np.asanyarray(X)
 
         if X.ndim != 2:
             raise ValueError('expected 2-d ndarray or matrix, not %d-d'
@@ -336,7 +336,15 @@ def matmat(self, X):
             raise ValueError('dimension mismatch: %r, %r'
                              % (self.shape, X.shape))
 
-        Y = self._matmat(X)
+        try:
+            Y = self._matmat(X)
+        except Exception as e:
+            if isspmatrix(X) or is_pydata_spmatrix(X):
+                raise TypeError(
+                    "Unable to multiply a LinearOperator with a sparse matrix."
+                    " Wrap the matrix in aslinearoperator first."
+                ) from e
+            raise
 
         if isinstance(Y, np.matrix):
             Y = asmatrix(Y)
@@ -365,8 +373,8 @@ def rmatmat(self, X):
         This rmatmat wraps the user-specified rmatmat routine.
 
         """
-
-        X = np.asanyarray(X)
+        if not (isspmatrix(X) or is_pydata_spmatrix(X)):
+            X = np.asanyarray(X)
 
         if X.ndim != 2:
             raise ValueError('expected 2-d ndarray or matrix, not %d-d'
@@ -376,7 +384,16 @@ def rmatmat(self, X):
             raise ValueError('dimension mismatch: %r, %r'
                              % (self.shape, X.shape))
 
-        Y = self._rmatmat(X)
+        try:
+            Y = self._rmatmat(X)
+        except Exception as e:
+            if isspmatrix(X) or is_pydata_spmatrix(X):
+                raise TypeError(
+                    "Unable to multiply a LinearOperator with a sparse matrix."
+                    " Wrap the matrix in aslinearoperator() first."
+                ) from e
+            raise
+
         if isinstance(Y, np.matrix):
             Y = asmatrix(Y)
         return Y
@@ -414,7 +431,9 @@ def dot(self, x):
         elif n
```

## Moved from `brief.md`

## Files That May Need Changes

- `scipy/sparse/linalg/_interface.py`
