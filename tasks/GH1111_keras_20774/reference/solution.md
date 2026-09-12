# Reference solution — GH1111_keras_20774

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1111_keras_20774`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1111_keras_20774/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `keras/src/backend/torch/nn.py` (modified, +95/-67)
- `keras/src/layers/pooling/average_pooling_test.py` (modified, +1/-0)
- `keras/src/ops/nn_test.py` (modified, +12/-0)

## Diff Summary (What the Fix Changes)

### `keras/src/backend/torch/nn.py`
```diff
@@ -2,7 +2,6 @@
 import torch.nn.functional as tnn
 
 from keras.src import backend
-from keras.src import tree
 from keras.src.backend.common.backend_utils import (
     compute_conv_transpose_padding_args_for_torch,
 )
@@ -204,17 +203,27 @@ def sparsemax(logits, axis=-1):
 def _compute_padding_length(
     input_length, kernel_length, stride, dilation_rate=1
 ):
-    """Compute padding length along one dimension."""
-    total_padding_length = (
-        dilation_rate * (kernel_length - 1) - (input_length - 1) % stride
-    )
-    left_padding = total_padding_length // 2
-    right_padding = (total_padding_length + 1) // 2
+    """Compute padding length along one dimension with support
+    for asymmetric padding."""
+    effective_k_size = (kernel_length - 1) * dilation_rate + 1
+    if stride == 1:
+        # total padding is kernel_size - 1
+        total_padding = effective_k_size - 1
+    else:
+        # calc. needed padding for case with stride involved
+        output_size = (input_length + stride - 1) // stride
+        total_padding = max(
+            0, (output_size - 1) * stride + effective_k_size - input_length
+        )
+
+    # divide padding evenly, with extra pixel going at the end if needed
+    left_padding = total_padding // 2
+    right_padding = total_padding - left_padding
     return (left_padding, right_padding)
 
 
 def _apply_same_padding(
-    inputs, kernel_size, strides, operation_type, dilation_rate=1
+    inputs, kernel_size, strides, data_format, operation_type, dilation_rate=1
 ):
     """Apply same padding to the input tensor.
 
@@ -231,50 +240,49 @@ def _apply_same_padding(
     """
     spatial_shape = inputs.shape[2:]
     num_spatial_dims = len(spatial_shape)
-    padding = ()
+    padding = []
+
+    if operation_type != "pooling":
+        dilation_rate = standardize_tuple(
+            dilation_rate, num_spatial_dims, "dilation_rate"
+        )
 
     for i in range(num_spatial_dims):
-        if operation_type == "pooli
```

## Moved from `brief.md`

## Files That May Need Changes

- `keras/src/backend/torch/nn.py`
