# Reference solution — GH1109_keras_22477

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1109_keras_22477`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1109_keras_22477/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `keras/src/layers/rnn/conv_lstm.py` (modified, +8/-0)
- `keras/src/layers/rnn/conv_lstm1d_test.py` (modified, +15/-0)
- `keras/src/layers/rnn/conv_lstm2d_test.py` (modified, +15/-0)
- `keras/src/layers/rnn/conv_lstm3d_test.py` (modified, +15/-0)

## Diff Summary (What the Fix Changes)

### `keras/src/layers/rnn/conv_lstm.py`
```diff
@@ -130,6 +130,14 @@ def __init__(
         self.dilation_rate = argument_validation.standardize_tuple(
             dilation_rate, self.rank, "dilation_rate"
         )
+        if max(self.strides) > 1 and max(self.dilation_rate) > 1:
+            raise ValueError(
+                "Specifying `strides > 1` is not compatible with "
+                "`dilation_rate > 1`. Please provide `strides=1` or "
+                "`dilation_rate=1`. "
+                f"Received: strides={self.strides} and "
+                f"dilation_rate={self.dilation_rate}"
+            )
         self.activation = activations.get(activation)
         self.recurrent_activation = activations.get(recurrent_activation)
         self.use_bias = use_bias
```

## Moved from `brief.md`

## Files That May Need Changes

- `keras/src/layers/rnn/conv_lstm.py`
