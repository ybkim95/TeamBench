# Reference solution — GH872_scipy_24778

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH872_scipy_24778`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH872_scipy_24778/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `scipy/spatial/transform/_rotation.py` (modified, +17/-11)
- `scipy/spatial/transform/tests/test_rotation.py` (modified, +2/-0)

## Diff Summary (What the Fix Changes)

### `scipy/spatial/transform/_rotation.py`
```diff
@@ -59,11 +59,11 @@ def _promote(*args: tuple[ArrayLike, ...], xp: ModuleType) -> Array:
     return xp_promote(*args, force_floating=True, xp=xp)
 
 
-rotation_extra_note = (
-    """The methods ``as_davenport``, ``apply``, and ``align_vectors``
+rotation_extra_note = """The methods ``as_davenport``, ``apply``, and ``align_vectors``
     are not supported with cupy<14.*.
 
-    """)
+    """
+
 
 @xp_capabilities(
     skip_backends=[("dask.array", "missing linalg.cross/det functions")],
@@ -401,7 +401,7 @@ class Rotation:
     output formats supported, consult the individual method's examples.
 
     """
-    
+
     # generic type compatibility with scipy-stubs
     __class_getitem__ = classmethod(GenericAlias)
 
@@ -1952,7 +1952,7 @@ def magnitude(self) -> Array:
 
     def approx_equal(
         self, other: Rotation, atol: float | None = None, degrees: bool = False
-    ) -> Array:
+    ) -> Array | np.bool:
         """Determine if another rotation is approximately equal to this one.
 
         Equality is measured by calculating the smallest angle between the
@@ -1972,10 +1972,10 @@ def approx_equal(
 
         Returns
         -------
-        approx_equal : ndarray or bool
-            Whether the rotations are approximately equal, bool if object
-            contains a single rotation and ndarray if object contains multiple
-            rotations.
+        approx_equal : Array or `numpy.bool`
+            Whether the rotations are approximately equal, `numpy.bool` if object
+            contains a single numpy rotation and Array if object contains multiple
+            rotations or is from another library.
 
         Examples
         --------
@@ -1989,11 +1989,16 @@ def approx_equal(
         Approximate equality for a single rotation:
 
         >>> p.approx_equal(q[0])
-        False
+        np.False_
         """
         cython_compatible = self._quat.ndim < 3 and other._quat.ndim < 3
         backend = select_backend(self._xp, cython_compatible=cyt
```

## Moved from `brief.md`

## Files That May Need Changes

- `scipy/spatial/transform/_rotation.py`
