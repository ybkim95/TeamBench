# Reference solution — GH1173_pytorch_164368

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1173_pytorch_164368`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1173_pytorch_164368/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `test/inductor/test_flex_attention.py` (modified, +80/-7)
- `torch/nn/attention/flex_attention.py` (modified, +9/-0)

## Diff Summary (What the Fix Changes)

### `torch/nn/attention/flex_attention.py`
```diff
@@ -649,6 +649,15 @@ def causal_mask(b, h, q_idx, kv_idx):
                 assert new_block_mask.kv_num_blocks.shape == (2, 1, 1)
                 assert new_block_mask.kv_indices.shape == (2, 1, 1, 4)
         """
+        index = (index,) if not isinstance(index, tuple) else index
+        padded = (*index, slice(None), slice(None), slice(None))[:3]
+        sizes = self.kv_num_blocks.shape[:3]
+        index = tuple(
+            (slice(i + n, i + n + 1) if -n <= i < 0 else slice(i, i + 1))
+            if isinstance(i, int)
+            else i
+            for i, n in zip(padded, sizes)
+        )
         new_kv_num_blocks = self.kv_num_blocks[index]
         new_kv_indices = self.kv_indices[index]
         if self.full_kv_num_blocks is not None:
```

## Moved from `brief.md`

## Files That May Need Changes

- `torch/nn/attention/flex_attention.py`
