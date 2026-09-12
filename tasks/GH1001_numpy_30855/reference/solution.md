# Reference solution — GH1001_numpy_30855

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1001_numpy_30855`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1001_numpy_30855/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `numpy/ma/core.py` (modified, +1/-1)
- `numpy/ma/tests/test_core.py` (modified, +7/-0)

## Diff Summary (What the Fix Changes)

### `numpy/ma/core.py`
```diff
@@ -2590,7 +2590,7 @@ def flatten_sequence(iterable):
 
         """
         for elm in iter(iterable):
-            if hasattr(elm, '__iter__'):
+            if hasattr(elm, "__iter__") and not isinstance(elm, (str, bytes)):
                 yield from flatten_sequence(elm)
             else:
                 yield elm
```

## Moved from `brief.md`

## Files That May Need Changes

- `numpy/ma/core.py`
