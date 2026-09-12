# Reference solution — GH1022_keras_20768

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1022_keras_20768`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1022_keras_20768/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `keras/src/backend/tensorflow/image.py` (modified, +39/-30)
- `keras/src/ops/image_test.py` (modified, +52/-0)

## Diff Summary (What the Fix Changes)

### `keras/src/backend/tensorflow/image.py`
```diff
@@ -431,23 +431,9 @@ def map_coordinates(
             f" Received input with shape: {coordinate_arrs.shape}"
         )
 
-    # unstack into a list of tensors for following operations
-    coordinate_arrs = tf.unstack(coordinate_arrs, axis=0)
-    fill_value = convert_to_tensor(tf.cast(fill_value, input_arr.dtype))
-
-    index_fixer = _INDEX_FIXERS.get(fill_mode)
-    if index_fixer is None:
-        raise ValueError(
-            "Invalid value for argument `fill_mode`. Expected one of "
-            f"{set(_INDEX_FIXERS.keys())}. Received: "
-            f"fill_mode={fill_mode}"
-        )
+    fill_value = convert_to_tensor(fill_value, dtype=input_arr.dtype)
 
-    def is_valid(index, size):
-        if fill_mode == "constant":
-            return (0 <= index) & (index < size)
-        else:
-            return True
+    coordinate_arrs = tf.unstack(coordinate_arrs, axis=0)
 
     if order == 0:
         interp_fun = _nearest_indices_and_weights
@@ -456,38 +442,61 @@ def is_valid(index, size):
     else:
         raise NotImplementedError("map_coordinates currently requires order<=1")
 
+    def process_coordinates(coords, size):
+        if fill_mode == "constant":
+            valid = (coords >= 0) & (coords < size)
+            safe_coords = tf.clip_by_value(coords, 0, size - 1)
+            return safe_coords, valid
+        elif fill_mode == "nearest":
+            return tf.clip_by_value(coords, 0, size - 1), tf.ones_like(
+                coords, dtype=tf.bool
+            )
+        elif fill_mode in ["mirror", "reflect"]:
+            coords = tf.abs(coords)
+            size_2 = size * 2
+            mod = tf.math.mod(coords, size_2)
+            under = mod < size
+            over = ~under
+            # reflect mode is same as mirror for under
+            coords = tf.where(under, mod, size_2 - mod)
+            # for reflect mode, adjust the over case
+            if fill_mode == "reflect":
+                coords = tf.where(over, coords - 1, coo
```

## Moved from `brief.md`

## Files That May Need Changes

- `keras/src/backend/tensorflow/image.py`
