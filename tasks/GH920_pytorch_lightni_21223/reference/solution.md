# Reference solution — GH920_pytorch_lightni_21223

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH920_pytorch_lightni_21223`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH920_pytorch_lightni_21223/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/lightning/pytorch/CHANGELOG.md` (modified, +3/-0)
- `src/lightning/pytorch/callbacks/pruning.py` (modified, +1/-1)
- `tests/tests_pytorch/callbacks/test_pruning.py` (modified, +94/-6)

## Diff Summary (What the Fix Changes)

### `src/lightning/pytorch/callbacks/pruning.py`
```diff
@@ -349,7 +349,7 @@ def apply_pruning(self, amount: Union[int, float]) -> None:
     def _log_sparsity_stats(
         self, prev: list[tuple[int, int]], curr: list[tuple[int, int]], amount: Union[int, float] = 0
     ) -> None:
-        total_params = sum(p.numel() for layer, _ in self._parameters_to_prune for p in layer.parameters())
+        total_params = sum(total for _, total in curr)
         prev_total_zeros = sum(zeros for zeros, _ in prev)
         curr_total_zeros = sum(zeros for zeros, _ in curr)
         log.info(
```

## Moved from `brief.md`

## Files That May Need Changes

- `src/lightning/pytorch/callbacks/pruning.py`
