# Reference solution — GH1023_pytorch_lightni_21187

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1023_pytorch_lightni_21187`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1023_pytorch_lightni_21187/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/lightning/pytorch/CHANGELOG.md` (modified, +1/-1)
- `src/lightning/pytorch/tuner/batch_size_scaling.py` (modified, +16/-2)
- `tests/tests_pytorch/tuner/test_scale_batch_size.py` (modified, +54/-4)

## Diff Summary (What the Fix Changes)

### `src/lightning/pytorch/tuner/batch_size_scaling.py`
```diff
@@ -178,14 +178,22 @@ def _run_power_scaling(
     # this flag is used to determine whether the previously scaled batch size, right before OOM, was a success or not
     # if it was we exit, else we continue downscaling in case we haven't encountered a single optimal batch size
     any_success = False
-    for _ in range(max_trials):
+    last_successful_size = new_size
+    for i in range(max_trials):
         garbage_collection_cuda()
 
         # reset after each try
         _reset_progress(trainer)
 
         try:
             _try_loop_run(trainer, params)
+            last_successful_size = new_size  # Store the current size before doubling
+
+            # Check if this is the last trial before trying to double
+            if i + 1 >= max_trials:
+                new_size = last_successful_size
+                break
+
             new_size, changed = _adjust_batch_size(trainer, batch_arg_name, factor=2.0, desc="succeeded")
 
             if not changed:
@@ -224,6 +232,7 @@ def _run_binary_scaling(
     low = 1
     high = None
     count = 0
+    last_successful_size = new_size
     while True:
         garbage_collection_cuda()
 
@@ -233,9 +242,14 @@ def _run_binary_scaling(
         try:
             # run loop
             _try_loop_run(trainer, params)
+            last_successful_size = new_size  # Store the current size before doubling
             count += 1
-            if count > max_trials:
+
+            # Check if we've reached max_trials before trying to adjust batch size
+            if count >= max_trials:
+                new_size = last_successful_size
                 break
+
             # Double in size
             low = new_size
             if high:
```

## Moved from `brief.md`

## Files That May Need Changes

- `src/lightning/pytorch/tuner/batch_size_scaling.py`
