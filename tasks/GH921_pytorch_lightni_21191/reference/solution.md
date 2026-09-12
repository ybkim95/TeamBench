# Reference solution — GH921_pytorch_lightni_21191

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH921_pytorch_lightni_21191`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH921_pytorch_lightni_21191/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/lightning/pytorch/CHANGELOG.md` (modified, +2/-0)
- `src/lightning/pytorch/callbacks/pruning.py` (modified, +2/-1)
- `tests/tests_pytorch/callbacks/test_pruning.py` (modified, +59/-1)

## Diff Summary (What the Fix Changes)

### `src/lightning/pytorch/callbacks/pruning.py`
```diff
@@ -277,7 +277,8 @@ def make_pruning_permanent(self, module: nn.Module) -> None:
 
     @staticmethod
     def _copy_param(new: nn.Module, old: nn.Module, name: str) -> None:
-        dst = getattr(new, name)
+        # Check if the parameter has been pruned (has _orig suffix)
+        dst = getattr(new, name + "_orig") if hasattr(new, name + "_orig") else getattr(new, name)
         src = getattr(old, name)
         if dst is None or src is None or not isinstance(dst, Tensor) or not isinstance(src, Tensor):
             return
```

## Moved from `brief.md`

## Files That May Need Changes

- `src/lightning/pytorch/callbacks/pruning.py`
