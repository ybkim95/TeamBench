# Reference solution — GH1078_ultralytics_23546

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1078_ultralytics_23546`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1078_ultralytics_23546/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `tests/test_cuda.py` (modified, +1/-0)
- `ultralytics/utils/autobatch.py` (modified, +2/-1)

## Diff Summary (What the Fix Changes)

### `ultralytics/utils/autobatch.py`
```diff
@@ -84,8 +84,9 @@ def autobatch(
 
     # Profile batch sizes
     batch_sizes = [1, 2, 4, 8, 16] if t < 16 else [1, 2, 4, 8, 16, 32, 64]
+    ch = model.yaml.get("channels", 3)
     try:
-        img = [torch.empty(b, 3, imgsz, imgsz) for b in batch_sizes]
+        img = [torch.empty(b, ch, imgsz, imgsz) for b in batch_sizes]
         results = profile_ops(img, model, n=1, device=device, max_num_obj=max_num_obj)
 
         # Fit a solution
```

## Moved from `brief.md`

## Files That May Need Changes

- `ultralytics/utils/autobatch.py`
