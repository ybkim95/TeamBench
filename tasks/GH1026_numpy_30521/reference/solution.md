# Reference solution — GH1026_numpy_30521

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1026_numpy_30521`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1026_numpy_30521/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `numpy/_core/numeric.py` (modified, +14/-1)
- `numpy/_core/tests/test_numeric.py` (modified, +6/-0)

## Diff Summary (What the Fix Changes)

### `numpy/_core/numeric.py`
```diff
@@ -1022,7 +1022,8 @@ def tensordot(a, b, axes=2):
         * (2,) array_like
           Or, a list of axes to be summed over, first sequence applying to `a`,
           second to `b`. Both elements array_like must be of the same length.
-
+          Each axis may appear at most once; repeated axes are not allowed.
+          For example, ``axes=([1, 1], [0, 0])`` is invalid.
     Returns
     -------
     output : ndarray
@@ -1053,6 +1054,13 @@ def tensordot(a, b, axes=2):
     first in both sequences, the second axis second, and so forth.
     The calculation can be referred to ``numpy.einsum``.
 
+    For example, if ``a.shape == (2, 3, 4)`` and ``b.shape == (3, 4, 5)``,
+    then ``axes=([1, 2], [0, 1])`` sums over the ``(3, 4)`` dimensions of
+    both arrays and produces an output of shape ``(2, 5)``.
+
+    Each summation axis corresponds to a distinct contraction index; repeating
+    an axis (for example ``axes=([1, 1], [0, 0])``) is invalid.
+
     The shape of the result consists of the non-contracted axes of the
     first tensor, followed by the non-contracted axes of the second.
 
@@ -1170,6 +1178,11 @@ def tensordot(a, b, axes=2):
         axes_b = [axes_b]
         nb = 1
 
+    if len(set(axes_a)) != len(axes_a):
+        raise ValueError("duplicate axes are not allowed in tensordot")
+    if len(set(axes_b)) != len(axes_b):
+        raise ValueError("duplicate axes are not allowed in tensordot")
+
     a, b = asarray(a), asarray(b)
     as_ = a.shape
     nda = a.ndim
```

## Moved from `brief.md`

## Files That May Need Changes

- `numpy/_core/numeric.py`
