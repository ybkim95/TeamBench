# Reference solution — GH1099_darts_2987

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1099_darts_2987`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1099_darts_2987/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.md` (modified, +1/-0)
- `darts/tests/utils/torch_datasets/test_torch_datasets.py` (modified, +64/-0)
- `darts/utils/data/torch_datasets/training_dataset.py` (modified, +17/-12)

## Diff Summary (What the Fix Changes)

### `darts/utils/data/torch_datasets/training_dataset.py`
```diff
@@ -170,19 +170,24 @@ def __init__(
 
         size_of_both_chunks = max(input_chunk_length, shift + output_chunk_length)
 
-        # setup samples
-        if max_samples_per_ts is None:
-            # read all time series to get the maximum size
-            max_samples_per_ts = max(len(ts) for ts in series) - size_of_both_chunks + 1
-            if max_samples_per_ts <= 0:
-                raise_log(
-                    ValueError(
-                        f"The input `series` are too short to extract even a single sample. "
-                        f"Expected min length: `{size_of_both_chunks}`, received max length: "
-                        f"`{max_samples_per_ts + size_of_both_chunks - 1}`."
-                    )
+        # compute the maximum available samples over all series
+        max_available_indices = max(len(ts) for ts in series) - size_of_both_chunks + 1
+        max_available_samples = ceil(max_available_indices / stride)
+
+        if max_available_indices <= 0:
+            raise_log(
+                ValueError(
+                    f"The input `series` are too short to extract even a single sample. "
+                    f"Expected min length: `{size_of_both_chunks}`, received max length: "
+                    f"`{max(len(ts) for ts in series)}`."
                 )
-            max_samples_per_ts = ceil(max_samples_per_ts / stride)
+            )
+
+        if max_samples_per_ts is None:
+            max_samples_per_ts = max_available_samples
+        else:
+            # upper bound maximum available samples by max_samples_per_ts
+            max_samples_per_ts = min(max_samples_per_ts, max_available_samples)
 
         self.input_chunk_length = input_chunk_length
         self.output_chunk_length = output_chunk_length
```

## Moved from `brief.md`

## Files That May Need Changes

- `darts/utils/data/torch_datasets/training_dataset.py`
