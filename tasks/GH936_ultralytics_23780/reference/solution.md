# Reference solution — GH936_ultralytics_23780

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH936_ultralytics_23780`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH936_ultralytics_23780/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `tests/test_cuda.py` (modified, +1/-0)
- `ultralytics/models/sam/predict.py` (modified, +4/-2)

## Diff Summary (What the Fix Changes)

### `ultralytics/models/sam/predict.py`
```diff
@@ -454,9 +454,11 @@ def setup_model(self, model=None, verbose=True):
         device = select_device(self.args.device, verbose=verbose)
         if model is None:
             model = self.get_model()
-        model.eval()
+        # Move model to device first, then cast dtype, then set eval so any eval-time caches are created on-device.
         model = model.to(device)
-        self.model = model.half() if self.args.half else model.float()
+        model = model.half() if self.args.half else model.float()
+        model.eval()
+        self.model = model
         self.device = device
         self.mean = torch.tensor([123.675, 116.28, 103.53]).view(-1, 1, 1).to(device)
         self.std = torch.tensor([58.395, 57.12, 57.375]).view(-1, 1, 1).to(device)
```

## Moved from `brief.md`

## Files That May Need Changes

- `ultralytics/models/sam/predict.py`
