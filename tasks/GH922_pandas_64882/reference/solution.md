# Reference solution — GH922_pandas_64882

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH922_pandas_64882`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH922_pandas_64882/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/source/whatsnew/v3.0.2.rst` (modified, +1/-0)
- `pandas/core/indexes/range.py` (modified, +7/-8)
- `pandas/tests/frame/methods/test_sort_index.py` (modified, +7/-0)

## Diff Summary (What the Fix Changes)

### `pandas/core/indexes/range.py`
```diff
@@ -772,8 +772,7 @@ def equals(self, other: object) -> bool:
             return self._range == other._range
         return super().equals(other)
 
-    # error: Signature of "sort_values" incompatible with supertype "Index"
-    @overload  # type: ignore[override]
+    @overload
     def sort_values(
         self,
         *,
@@ -791,7 +790,7 @@ def sort_values(
         ascending: bool = ...,
         na_position: NaPosition = ...,
         key: Callable | None = ...,
-    ) -> tuple[Self, np.ndarray | RangeIndex]: ...
+    ) -> tuple[Self, np.ndarray]: ...
 
     @overload
     def sort_values(
@@ -801,7 +800,7 @@ def sort_values(
         ascending: bool = ...,
         na_position: NaPosition = ...,
         key: Callable | None = ...,
-    ) -> Self | tuple[Self, np.ndarray | RangeIndex]: ...
+    ) -> Self | tuple[Self, np.ndarray]: ...
 
     def sort_values(
         self,
@@ -810,7 +809,7 @@ def sort_values(
         ascending: bool = True,
         na_position: NaPosition = "last",
         key: Callable | None = None,
-    ) -> Self | tuple[Self, np.ndarray | RangeIndex]:
+    ) -> Self | tuple[Self, np.ndarray]:
         if key is not None:
             return super().sort_values(
                 return_indexer=return_indexer,
@@ -831,10 +830,10 @@ def sort_values(
 
         if return_indexer:
             if inverse_indexer:
-                rng = range(len(self) - 1, -1, -1)
+                indexer = np.arange(len(self) - 1, -1, -1, dtype=np.intp)
             else:
-                rng = range(len(self))
-            return sorted_index, RangeIndex(rng)
+                indexer = np.arange(len(self), dtype=np.intp)
+            return sorted_index, indexer
         else:
             return sorted_index
 
```

## Moved from `brief.md`

## Files That May Need Changes

- `pandas/core/indexes/range.py`
