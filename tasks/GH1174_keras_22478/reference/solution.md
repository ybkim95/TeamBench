# Reference solution — GH1174_keras_22478

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1174_keras_22478`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1174_keras_22478/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `keras/src/ops/image.py` (modified, +14/-0)
- `keras/src/ops/image_test.py` (modified, +58/-0)

## Diff Summary (What the Fix Changes)

### `keras/src/ops/image.py`
```diff
@@ -98,6 +98,13 @@ def compute_output_spec(self, images):
                 "Invalid images dtype: expected float dtype. "
                 f"Received: images.dtype={dtype}"
             )
+        channels_axis = -1 if self.data_format == "channels_last" else -3
+        channels = images_shape[channels_axis]
+        if channels is not None and channels != 3:
+            raise ValueError(
+                "Input images must have 3 channels, but received images with "
+                f"{channels} channels."
+            )
         return KerasTensor(shape=images_shape, dtype=images.dtype)
 
 
@@ -170,6 +177,13 @@ def compute_output_spec(self, images):
                 "Invalid images dtype: expected float dtype. "
                 f"Received: images.dtype={dtype}"
             )
+        channels_axis = -1 if self.data_format == "channels_last" else -3
+        channels = images_shape[channels_axis]
+        if channels is not None and channels != 3:
+            raise ValueError(
+                "Input images must have 3 channels, but received images with "
+                f"{channels} channels."
+            )
         return KerasTensor(shape=images_shape, dtype=images.dtype)
 
 
```

## Moved from `brief.md`

## Files That May Need Changes

- `keras/src/ops/image.py`
