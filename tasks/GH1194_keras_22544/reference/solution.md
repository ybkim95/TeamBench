# Reference solution — GH1194_keras_22544

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1194_keras_22544`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1194_keras_22544/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `keras/src/backend/tensorflow/numpy.py` (modified, +4/-0)
- `keras/src/backend/torch/numpy.py` (modified, +3/-0)
- `keras/src/ops/numpy.py` (modified, +6/-0)
- `keras/src/ops/numpy_test.py` (modified, +3/-0)

## Diff Summary (What the Fix Changes)

### `keras/src/backend/tensorflow/numpy.py`
```diff
@@ -2867,6 +2867,10 @@ def sort(x, axis=-1):
     x = convert_to_tensor(x)
     ori_dtype = standardize_dtype(x.dtype)
     # TODO: tf.sort doesn't support bool
+    if axis is None:
+        x = tf.reshape(x, [-1])
+        axis = 0
+
     if ori_dtype == "bool":
         x = tf.cast(x, "int8")
         return tf.cast(tf.sort(x, axis=axis), ori_dtype)
```

### `keras/src/backend/torch/numpy.py`
```diff
@@ -1820,6 +1820,9 @@ def size(x):
 
 def sort(x, axis=-1):
     x = convert_to_tensor(x)
+    if axis is None:
+        x = x.reshape(-1)
+        axis = 0
     # TODO: torch.sort doesn't support bool with cuda
     if get_device() == "cuda" and standardize_dtype(x.dtype) == "bool":
         x = cast(x, "uint8")
```

### `keras/src/ops/numpy.py`
```diff
@@ -7275,6 +7275,12 @@ def call(self, x):
         return backend.numpy.sort(x, axis=self.axis)
 
     def compute_output_spec(self, x):
+        if self.axis is None:
+            if None in x.shape:
+                output_shape = (None,)
+            else:
+                output_shape = (int(np.prod(x.shape)),)
+            return KerasTensor(output_shape, x.dtype)
         return KerasTensor(x.shape, x.dtype)
 
 
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `keras/src/backend/tensorflow/numpy.py`
- `keras/src/backend/torch/numpy.py`
- `keras/src/ops/numpy.py`
