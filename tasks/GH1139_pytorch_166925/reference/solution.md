# Reference solution — GH1139_pytorch_166925

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1139_pytorch_166925`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1139_pytorch_166925/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `test/dynamo/test_decorators.py` (modified, +17/-0)
- `torch/_dynamo/symbolic_convert.py` (modified, +13/-0)

## Diff Summary (What the Fix Changes)

### `torch/_dynamo/symbolic_convert.py`
```diff
@@ -1355,6 +1355,19 @@ def step(self) -> bool:
         except (ReturnValueOp, YieldValueOp):
             return False
         except Unsupported:
+            # More restrictive condition than should_compile_partial_graph:
+            # if this condition is true, then we SHOULD NOT attempt to find
+            # a previous checkpoint to resume from and try to resume - we should
+            # immediately error out.
+            # The condition is more restrictive because, it may be possible to resume significantly earlier
+            # in the code (the most recent speculation point). This happens, for example, in the case
+            # of a graph break in a try block.
+            if (
+                self.one_graph
+                or self.error_on_graph_break
+                or self.is_tracing_resume_prologue
+            ):
+                raise
             if self.current_speculation is None:
                 log.debug("empty checkpoint")
                 raise
```

## Moved from `brief.md`

## Files That May Need Changes

- `torch/_dynamo/symbolic_convert.py`
