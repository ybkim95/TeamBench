# Reference solution — GH1193_pytorch_170884

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1193_pytorch_170884`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1193_pytorch_170884/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `test/inductor/test_compiled_autograd.py` (modified, +8/-2)
- `test/inductor/test_cudagraph_trees.py` (modified, +153/-23)
- `torch/_inductor/compile_fx.py` (modified, +10/-1)
- `torch/_inductor/ir.py` (modified, +6/-1)
- `torch/_inductor/lowering.py` (modified, +25/-2)
- `torch/_inductor/scheduler.py` (modified, +50/-36)
- `torch/_inductor/utils.py` (modified, +107/-51)

## Diff Summary (What the Fix Changes)

### `torch/_inductor/compile_fx.py`
```diff
@@ -1598,9 +1598,11 @@ def codegen_and_compile(
                     # Collect and dump collective-op schedule for external diagnostics
                     torch._inductor.debug.log_collective_schedule(graph.scheduler.nodes)
 
+                    # When graph_partition is enabled, skip this check - partitioning handles dynamic shapes
                     if (
                         cudagraphs
                         and config.triton.cudagraph_skip_dynamic_graphs
+                        and not config.graph_partition
                         and not V.graph.disable_cudagraphs_reason
                         and torch._inductor.utils.any_is_symbolic(*example_inputs)
                     ):
@@ -1625,7 +1627,14 @@ def codegen_and_compile(
                         V.graph.disable_cudagraphs_reason = disable
 
                     # pyrefly: ignore [unbound-name]
-                    if cudagraphs and not V.graph.disable_cudagraphs_reason:
+                    # When graph_partition is enabled, skip this check - partitioning handles incompatible ops
+                    if (
+                        cudagraphs
+                        # pyrefly: ignore [unbound-name]
+                        and not config.graph_partition
+                        # pyrefly: ignore [unbound-name]
+                        and not V.graph.disable_cudagraphs_reason
+                    ):
                         maybe_incompat_node = get_first_incompatible_cudagraph_node(gm)
                         if maybe_incompat_node:
                             disable = f"disabling cudagraphs due to incompatible op {maybe_incompat_node.target}"
```

### `torch/_inductor/ir.py`
```diff
@@ -6052,8 +6052,13 @@ def unflatten_args(
             if not isinstance(example_output, (list, tuple))
             else example_output
         )
+        # When graph_partition is enabled, skip - partitioning handles sparse outputs
         for t in example_out_li:
-            if isinstance(t, torch.Tensor) and t.is_sparse:
+            if (
+                isinstance(t, torch.Tensor)
+                and t.is_sparse
+                and not config.graph_partition
+            ):
                 msg = "sparsity not handled. Please file issue for sparse inference weights."
                 if stack_trace := V.graph.current_node.meta.get("stack_trace", None):
                     msg = f"{msg} Found from : \n {stack_trace}"
```

### `torch/_inductor/lowering.py`
```diff
@@ -3923,7 +3923,24 @@ def index_put_as_masked_fill(self, indices, value, accumulate):
 
 
 def index_put_fallback(self, indices, values, accumulate):
+    from .utils import _fx_node_is_input_dependent_cudagraph_unsafe
+
     op_overload = getattr(aten.index_put_, V.graph.current_node.target._overloadname)  # type: ignore[union-attr]
+
+    # Check if any index is a boolean tensor - if so, mark as cudagraph-unsafe
+    # because boolean indices trigger .nonzero() during CUDA graph capture
+    # When graph_partition is enabled, skip - partitioning handles this
+    fx_node = V.graph.current_node
+    if (
+        not config.graph_partition
+        and fx_node is not None
+        and _fx_node_is_input_dependent_cudagraph_unsafe(fx_node)
+    ):
+        msg = "index_put_ fallback with boolean indexing is not compatible with CUDA graphs"
+        if stack_trace := fx_node.meta.get("stack_trace", None):
+            msg = f"{msg} Found from : \n {stack_trace}"
+        V.graph.disable_cudagraphs_reason = msg
+
     ir.IndexPutFallback(op_overload, self, indices, values, accumulate)
     return self
 
@@ -7282,7 +7299,11 @@ def triton_kernel_wrap_(
 
 
 @register_lowering(torch.ops.higher_order.cond, type_promotion_kind=None)
-def cond(pred, true_fn, false_fn, operands):
+def cond(
+    pred, true_fn, false_fn, operands
+) -> list[Union[ir.TensorBox, ir.ShapeAsConstantBuffer]]:
+    # TODO: when graph_partition is enabled, skip - partitioning handles control flow
+    # we run into memory cleanup issue
     if any(isinstance(x, IRNode) and is_triton(x) for x in [pred, *operands]):
         msg = "control flow operator: torch.cond."
         if stack_trace := V.graph.current_node.meta.get("stack_trace", None):
@@ -7295,7 +7316,9 @@ def cond(pred, true_fn, false_fn, operands):
 
 @register_lowering(torch.ops.higher_order.while_loop, type_promotion_kind=None)
 def while_loop(cond_fn, body_fn, carried_inputs, additional_inputs, stack_output=False):
-    if any(
+    # T
```

### `torch/_inductor/scheduler.py`
```diff
@@ -2717,6 +2717,43 @@ def used_non_deterministic_runtime_estimations() -> bool:
     return config.runtime_estimations_mms_benchmark
 
 
+def get_layout_symints(node: ir.IRNode) -> OrderedSet[sympy.Symbol]:
+    """Get free symbols from a node's layout (size, stride, offset)."""
+    free_symbol_uses: OrderedSet[sympy.Symbol] = OrderedSet()
+    layout = node.maybe_get_layout()
+    if isinstance(layout, ir.Layout):
+        free_symbol_uses.update(
+            free_symbols(layout.size)
+            | free_symbols(layout.stride)
+            | free_symbols(layout.offset)
+        )
+        if isinstance(layout, ir.MutationLayoutSHOULDREMOVE):
+            # symint may be used as index in layout.target
+            free_symbol_uses.update(get_layout_symints(layout.target))
+    else:
+        assert layout is None, f"Expect layout to be None but found layout={layout}"
+    return free_symbol_uses
+
+
+def get_scheduler_node_symbol_uses(
+    node: BaseSchedulerNode,
+) -> OrderedSet[sympy.Symbol]:
+    """
+    Gets symbols used in a scheduler node, including free symbols from
+    the node's operations and layout symints from outputs.
+    """
+    if isinstance(node, FusedSchedulerNode):
+        return OrderedSet().union(
+            *(get_scheduler_node_symbol_uses(snode) for snode in node.snodes)
+        )
+    assert node.node is not None
+    free_symbol_uses = node.node.get_free_symbol_uses()
+    free_symbol_uses.update(
+        *(get_layout_symints(ir_node) for ir_node in node.node.get_outputs())
+    )
+    return free_symbol_uses
+
+
 class Scheduler:
     """
     A Scheduler is a graph of BaseSchedulerNodes. It is responsible for
@@ -5472,7 +5509,12 @@ def should_partition(
         def noop_log(msg: str, node: Optional[BaseSchedulerNode]) -> None:
             return
 
-        log_partition_reason = maybe_log_cudagraph_partition if should_log else noop_log
+        # Don't log partition reasons for CPU-only graphs since cudagraph
+        # part
```

### `torch/_inductor/utils.py`
```diff
@@ -1162,57 +1162,33 @@ def any_is_symbolic(*args: Any) -> bool:
     return any(is_symbolic(a) for a in args)
 
 
+# Ops that are fundamentally incompatible with CUDA graph capture
+# (e.g., CPU synchronization, dynamic memory allocation, etc.)
+FORBIDDEN_CUDAGRAPH_OPS = frozenset(
+    [
+        "aten._fused_moving_avg_obs_fq_helper.default",
+        "aten._fused_moving_avg_obs_fq_helper_functional.default",
+        "fbgemm.dense_to_jagged.default",
+        "fbgemm.jagged_to_padded_dense.default",
+        "run_and_save_rng_state",
+        "run_with_rng_state",
+        "aten._local_scalar_dense",
+        # Technically, it's not necessary to ban this, because an
+        # assert_scalar with constant arguments can be validly run
+        # with CUDA graphs, but the operator is also pointless with
+        # constant arguments, so might as well ban
+        "aten._assert_scalar",
+    ]
+)
+
+
 def get_first_incompatible_cudagraph_node(
     gm: torch.fx.GraphModule,
 ) -> Optional[torch.fx.Node]:
     from torch.fx.experimental.symbolic_shapes import free_unbacked_symbols
 
-    forbidden_set = OrderedSet(
-        [
-            "aten._fused_moving_avg_obs_fq_helper.default",
-            "aten._fused_moving_avg_obs_fq_helper_functional.default",
-            "fbgemm.dense_to_jagged.default",
-            "fbgemm.jagged_to_padded_dense.default",
-            "run_and_save_rng_state",
-            "run_with_rng_state",
-            "aten._local_scalar_dense",
-            # Technically, it's not necessary to ban this, because an
-            # assert_scalar with constant arguments can be validly run
-            # with CUDA graphs, but the operator is also pointless with
-            # constant arguments, so might as well ban
-            "aten._assert_scalar",
-        ]
-    )
-    if torch.are_deterministic_algorithms_enabled():
-        forbidden_set.update(
-            (
-                "aten._unsafe_index_put.default",
-                "aten._unsafe_
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `torch/_inductor/compile_fx.py`
- `torch/_inductor/ir.py`
- `torch/_inductor/lowering.py`
- `torch/_inductor/scheduler.py`
- `torch/_inductor/utils.py`
