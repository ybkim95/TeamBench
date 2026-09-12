# Reference solution — GH1138_pytorch_166922

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1138_pytorch_166922`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1138_pytorch_166922/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `test/inductor/test_max_autotune.py` (modified, +23/-0)
- `torch/_inductor/kernel/bmm.py` (modified, +3/-2)

## Diff Summary (What the Fix Changes)

### `torch/_inductor/kernel/bmm.py`
```diff
@@ -208,9 +208,10 @@ def may_require_contiguous(t, meta_t):
             )
         )
 
-    if use_triton_template(layout, check_max_autotune=False):
+    if use_triton_template(layout, check_max_autotune=False) and (
+        out_dtype is None or out_dtype == mat1.get_dtype()
+    ):
         # TODO: add out_dtype support for Triton Template
-        assert out_dtype is None, "out_dtype is not supported for Triton"
 
         choices.extend(
             V.choices.get_mm_configs(kernel_inputs, layout, [bmm_template], name)
```

## Moved from `brief.md`

## Files That May Need Changes

- `torch/_inductor/kernel/bmm.py`
