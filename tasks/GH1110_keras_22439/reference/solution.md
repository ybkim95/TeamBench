# Reference solution — GH1110_keras_22439

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1110_keras_22439`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1110_keras_22439/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `keras/src/layers/convolutional/base_conv_transpose.py` (modified, +13/-0)
- `keras/src/layers/convolutional/conv_transpose_test.py` (modified, +24/-0)

## Diff Summary (What the Fix Changes)

### `keras/src/layers/convolutional/base_conv_transpose.py`
```diff
@@ -151,6 +151,19 @@ def __init__(
                 f"dilation_rate={self.dilation_rate}"
             )
 
+        if self.output_padding is not None:
+            for i, (op, s) in enumerate(zip(self.output_padding, self.strides)):
+                if op >= s:
+                    raise ValueError(
+                        "Invalid `output_padding` argument. "
+                        "Each value in `output_padding` must be strictly "
+                        "less than the corresponding `strides` value.\n"
+                        f"At index {i}, `output_padding` is {op} and `strides` "
+                        f"is {s}.\n"
+                        f"Received: output_padding={self.output_padding}, "
+                        f"strides={self.strides}."
+                    )
+
     def build(self, input_shape):
         if self.data_format == "channels_last":
             channel_axis = -1
```

## Moved from `brief.md`

## Files That May Need Changes

- `keras/src/layers/convolutional/base_conv_transpose.py`
