# Reference solution — GH881_pymc_7858

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH881_pymc_7858`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH881_pymc_7858/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `pymc/pytensorf.py` (modified, +2/-4)
- `tests/test_pytensorf.py` (modified, +28/-1)

## Diff Summary (What the Fix Changes)

### `pymc/pytensorf.py`
```diff
@@ -567,10 +567,8 @@ def __init__(self, f):
     def __call__(self, state):
         return self.f(**state)
 
-    def __getattr__(self, item):
-        """Allow access to the original function attributes."""
-        # This is only reached if `__getattribute__` fails.
-        return getattr(self.f, item)
+    def dprint(self, **kwrags):
+        return self.f.dprint(**kwrags)
 
 
 class CallableTensor:
```

## Moved from `brief.md`

## Files That May Need Changes

- `pymc/pytensorf.py`
