# Reference solution — GH1192_pytorch_171129

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1192_pytorch_171129`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1192_pytorch_171129/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `test/inductor/test_triton_kernels.py` (modified, +40/-3)
- `torch/_higher_order_ops/triton_kernel_wrap.py` (modified, +25/-16)

## Diff Summary (What the Fix Changes)

### `torch/_higher_order_ops/triton_kernel_wrap.py`
```diff
@@ -322,11 +322,6 @@ def is_stable_tensor_descriptor_arg(arg: Any) -> bool:
                 return True
         return False
 
-    def is_tensor_like_arg(arg: Any) -> bool:
-        if isinstance(arg, Tensor) or is_stable_tensor_descriptor_arg(arg):
-            return True
-        return False
-
     # Note: one would expect that each input to the triton kernel maps to
     # one input parameter in the TTIR. This is _not_ true for TMA descriptors:
     # one TMA descriptor gets converted into:
@@ -335,9 +330,13 @@ def is_tensor_like_arg(arg: Any) -> bool:
     #   * N sizes, for a rank-N tensor
     # To account for this, we inject some fake arg names as placeholders for
     # the stride and size parameters.
-    def get_tensor_names(name: str, arg: Any) -> list[str]:
-        if isinstance(arg, Tensor):
-            return [name]
+    #
+    # Tensors and scalars both become single TTIR parameters, whereas
+    # `constexpr` are inlined. This matters for "odd" ordering
+    # (eg. [tensor, scalar, tensor]).
+    def get_arg_names(name: str, arg: Any, is_constexpr) -> list[str]:
+        if is_constexpr or arg is None:
+            return []
         if is_stable_tensor_descriptor_arg(arg):
             stable_meta = maybe_unpack_tma_stable_metadata(
                 tma_descriptor_metadata[name]
@@ -349,11 +348,12 @@ def get_tensor_names(name: str, arg: Any) -> list[str]:
             names.extend(name + f" STRIDE PLACEHOLDER {i}" for i in range(tensor_rank))
             names.extend(name + f" SIZE PLACEHOLDER {i}" for i in range(tensor_rank))
             return names
-        return []
+        return [name]
 
-    ordered_tensor_names = list(
+    ordered_arg_names = list(
         itertools.chain.from_iterable(
-            get_tensor_names(name, arg) for name, arg in ordered_args.items()
+            get_arg_names(name, arg, param.is_constexpr)
+            for (name, arg), param in zip(ordered_args.items(), kernel.params)
         )
     )
 
@@ -440,8 
```

## Moved from `brief.md`

## Files That May Need Changes

- `torch/_higher_order_ops/triton_kernel_wrap.py`
