# Reference solution — GH917_transformers_37544

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH917_transformers_37544`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH917_transformers_37544/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/transformers/image_transforms.py` (modified, +1/-1)
- `tests/test_image_transforms.py` (modified, +19/-0)

## Diff Summary (What the Fix Changes)

### `src/transformers/image_transforms.py`
```diff
@@ -751,7 +751,7 @@ def _expand_for_data_format(values):
         values = ((0, 0), *values) if input_data_format == ChannelDimension.FIRST else (*values, (0, 0))
 
         # Add additional padding if there's a batch dimension
-        values = (0, *values) if image.ndim == 4 else values
+        values = ((0, 0), *values) if image.ndim == 4 else values
         return values
 
     padding = _expand_for_data_format(padding)
```

## Moved from `brief.md`

## Files That May Need Changes

- `src/transformers/image_transforms.py`
