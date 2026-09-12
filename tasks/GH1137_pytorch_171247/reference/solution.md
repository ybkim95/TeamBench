# Reference solution — GH1137_pytorch_171247

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1137_pytorch_171247`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1137_pytorch_171247/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `test/inductor/test_torchinductor.py` (modified, +11/-4)
- `torch/_inductor/utils.py` (modified, +2/-0)

## Diff Summary (What the Fix Changes)

### `torch/_inductor/utils.py`
```diff
@@ -3036,6 +3036,8 @@ def device_need_guard(device: str) -> bool:
 def needs_fallback_due_to_atomic_add_limitations(dtype: torch.dtype) -> bool:
     if dtype == torch.bfloat16 and torch.cuda.is_available():
         return torch.cuda.get_device_capability() < (9, 0)
+    elif dtype == torch.bfloat16 and torch.xpu.is_available():
+        return True
     else:
         return dtype in (torch.int64, torch.bool)
 
```

## Moved from `brief.md`

## Files That May Need Changes

- `torch/_inductor/utils.py`
