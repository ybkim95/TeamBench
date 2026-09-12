# Reference solution — GH892_dask_9871

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH892_dask_9871`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH892_dask_9871/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `dask/layers.py` (modified, +6/-6)
- `dask/tests/test_distributed.py` (modified, +21/-0)

## Diff Summary (What the Fix Changes)

### `dask/layers.py`
```diff
@@ -872,6 +872,8 @@ def __init__(
         rhs_npartitions,
         parts_out=None,
         annotations=None,
+        left_on=None,
+        right_on=None,
         **merge_kwargs,
     ):
         super().__init__(annotations=annotations)
@@ -882,14 +884,12 @@ def __init__(
         self.rhs_name = rhs_name
         self.rhs_npartitions = rhs_npartitions
         self.parts_out = parts_out or set(range(self.npartitions))
+        self.left_on = tuple(left_on) if isinstance(left_on, list) else left_on
+        self.right_on = tuple(right_on) if isinstance(right_on, list) else right_on
         self.merge_kwargs = merge_kwargs
         self.how = self.merge_kwargs.get("how")
-        self.left_on = self.merge_kwargs.get("left_on")
-        self.right_on = self.merge_kwargs.get("right_on")
-        if isinstance(self.left_on, list):
-            self.left_on = (list, tuple(self.left_on))
-        if isinstance(self.right_on, list):
-            self.right_on = (list, tuple(self.right_on))
+        self.merge_kwargs["left_on"] = self.left_on
+        self.merge_kwargs["right_on"] = self.right_on
 
     def get_output_keys(self):
         return {(self.name, part) for part in self.parts_out}
```

## Moved from `brief.md`

## Files That May Need Changes

- `dask/layers.py`
