# Reference solution — GH1065_gpytorch_2132

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1065_gpytorch_2132`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1065_gpytorch_2132/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `gpytorch/settings.py` (modified, +7/-7)
- `test/test_settings.py` (modified, +34/-0)

## Diff Summary (What the Fix Changes)

### `gpytorch/settings.py`
```diff
@@ -56,13 +56,13 @@ def _set_value(cls, float_value, double_value, half_value):
         if half_value is not None:
             cls._global_half_value = half_value
 
-    def __init__(self, float=None, double=None, half=None):
-        self._orig_float_value = self.__class__.value()
-        self._instance_float_value = float
-        self._orig_double_value = self.__class__.value()
-        self._instance_double_value = double
-        self._orig_half_value = self.__class__.value()
-        self._instance_half_value = half
+    def __init__(self, float_value=None, double_value=None, half_value=None):
+        self._orig_float_value = self.__class__.value(torch.float)
+        self._instance_float_value = float_value if float_value is not None else self._orig_float_value
+        self._orig_double_value = self.__class__.value(torch.double)
+        self._instance_double_value = double_value if double_value is not None else self._orig_double_value
+        self._orig_half_value = self.__class__.value(torch.half)
+        self._instance_half_value = half_value if half_value is not None else self._orig_half_value
 
     def __enter__(
         self,
```

## Moved from `brief.md`

## Files That May Need Changes

- `gpytorch/settings.py`
