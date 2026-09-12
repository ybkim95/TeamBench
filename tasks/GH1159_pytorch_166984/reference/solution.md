# Reference solution — GH1159_pytorch_166984

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1159_pytorch_166984`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1159_pytorch_166984/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `test/inductor/test_cudagraph_trees.py` (modified, +119/-0)
- `torch/_inductor/codegen/wrapper.py` (modified, +2/-1)
- `torch/_inductor/graph.py` (modified, +5/-2)

## Diff Summary (What the Fix Changes)

### `torch/_inductor/codegen/wrapper.py`
```diff
@@ -1700,7 +1700,8 @@ def memory_plan(self):
         self.lines = MemoryPlanner(self).plan(self.lines)
 
     def memory_plan_reuse(self):
-        out_names = V.graph.get_output_names()
+        outputs = self.get_graph_outputs()
+        out_names = V.graph._get_output_names(outputs)
 
         while (
             self.lines
```

### `torch/_inductor/graph.py`
```diff
@@ -2410,11 +2410,11 @@ def _compile_to_module_lines(
 
         return mod
 
-    def get_output_names(self) -> list[str]:
+    def _get_output_names(self, graph_outputs: list[ir.IRNode]) -> list[str]:
         names = []
         shape_counter = itertools.count(0)
         none_counter = itertools.count(0)
-        for node in self.graph_outputs:
+        for node in graph_outputs:
             if isinstance(node, ir.NoneAsConstantBuffer):
                 names.append(f"{self.name}_none{next(none_counter)}")
             elif isinstance(node, ir.ShapeAsConstantBuffer):
@@ -2423,6 +2423,9 @@ def get_output_names(self) -> list[str]:
                 names.append(node.get_name())
         return names
 
+    def get_output_names(self) -> list[str]:
+        return self._get_output_names(self.graph_outputs)
+
     def is_unspec_arg(self, name: str) -> bool:
         # dynamo wraps unspec variable as 0d CPU tensor,
         # need to convert to scalar during codegen (triton only)
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `torch/_inductor/codegen/wrapper.py`
- `torch/_inductor/graph.py`
