# Reference solution — GH1140_keras_21729

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1140_keras_21729`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1140_keras_21729/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `keras/src/backend/tensorflow/numpy.py` (modified, +9/-5)
- `keras/src/ops/numpy_test.py` (modified, +40/-1)

## Diff Summary (What the Fix Changes)

### `keras/src/backend/tensorflow/numpy.py`
```diff
@@ -3161,10 +3161,14 @@ def histogram(x, bins=10, range=None):
 
     x = tf.boolean_mask(x, (x >= min_val) & (x <= max_val))
     bin_edges = tf.linspace(min_val, max_val, bins + 1)
-    bin_edges_list = bin_edges.numpy().tolist()
-    bin_indices = tf.raw_ops.Bucketize(input=x, boundaries=bin_edges_list[1:-1])
-
-    bin_counts = tf.math.bincount(
-        bin_indices, minlength=bins, maxlength=bins, dtype=x.dtype
+    bin_edges = tf.cast(bin_edges, x.dtype)
+    bin_indices = tf.searchsorted(bin_edges[1:-1], x, side="right")
+
+    # tf.math.bincount does not work with XLA in this case. So, we use
+    # `scatter_nd`.
+    bin_counts = tf.scatter_nd(
+        indices=tf.expand_dims(bin_indices, axis=-1),
+        updates=tf.ones_like(bin_indices, dtype=x.dtype),
+        shape=(bins,),
     )
     return bin_counts, bin_edges
```

## Moved from `brief.md`

## Files That May Need Changes

- `keras/src/backend/tensorflow/numpy.py`
