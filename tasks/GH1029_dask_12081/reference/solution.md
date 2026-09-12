# Reference solution — GH1029_dask_12081

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1029_dask_12081`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1029_dask_12081/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `dask/_expr.py` (modified, +20/-17)
- `dask/tests/test_base.py` (modified, +11/-0)

## Diff Summary (What the Fix Changes)

### `dask/_expr.py`
```diff
@@ -1238,27 +1238,30 @@ def _simplify_down(self):
 
         issue_warning = False
         hlgs = []
-        for op in self.operands:
-            if isinstance(op, (HLGExpr, HLGFinalizeCompute)):
-                hlgs.append(op)
-            elif isinstance(op, dict):
-                hlgs.append(
-                    HLGExpr(
-                        dsk=HighLevelGraph.from_collections(
-                            str(id(op)), op, dependencies=()
+        if any(
+            isinstance(op, (HLGExpr, HLGFinalizeCompute, dict)) for op in self.operands
+        ):
+            for op in self.operands:
+                if isinstance(op, (HLGExpr, HLGFinalizeCompute)):
+                    hlgs.append(op)
+                elif isinstance(op, dict):
+                    hlgs.append(
+                        HLGExpr(
+                            dsk=HighLevelGraph.from_collections(
+                                str(id(op)), op, dependencies=()
+                            )
                         )
                     )
-                )
-            elif hlgs:
-                issue_warning = True
-                opt = op.optimize()
-                hlgs.append(
-                    HLGExpr(
-                        dsk=HighLevelGraph.from_collections(
-                            opt._name, opt.__dask_graph__(), dependencies=()
+                else:
+                    issue_warning = True
+                    opt = op.optimize()
+                    hlgs.append(
+                        HLGExpr(
+                            dsk=HighLevelGraph.from_collections(
+                                opt._name, opt.__dask_graph__(), dependencies=()
+                            )
                         )
                     )
-                )
         if issue_warning:
             warnings.warn(
                 "Computing mixed collections that are backed by "
```

## Moved from `brief.md`

## Files That May Need Changes

- `dask/_expr.py`
