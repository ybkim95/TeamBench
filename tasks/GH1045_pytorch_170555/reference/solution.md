# Reference solution — GH1045_pytorch_170555

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1045_pytorch_170555`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1045_pytorch_170555/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `test/inductor/test_flex_attention.py` (modified, +25/-0)
- `torch/_dynamo/variables/higher_order_ops.py` (modified, +3/-6)

## Diff Summary (What the Fix Changes)

### `torch/_dynamo/variables/higher_order_ops.py`
```diff
@@ -3899,13 +3899,10 @@ def _call_function(
         score_mod_node, score_mod_lifted_args = self.create_wrapped_node(
             tx, query, score_mod, "score_mod"
         )
-        mask_fn = block_mask.items[-1]
-        if mask_fn.is_python_constant():
-            mask_callable = mask_fn.as_python_constant()
-            if mask_callable is None:
-                mask_callable = torch.nn.attention.flex_attention.noop_mask
+        mask_fn = block_mask.items[-1]  # type: ignore[attr-defined]
+        if mask_fn.is_python_constant() and mask_fn.as_python_constant() is None:
             mask_fn = UserFunctionVariable(
-                mask_callable,
+                torch.nn.attention.flex_attention.noop_mask,
                 source=mask_fn.source,
             )
         mask_fn_node, mask_fn_lifted_args = self.create_wrapped_node(
```

## Moved from `brief.md`

## Files That May Need Changes

- `torch/_dynamo/variables/higher_order_ops.py`
