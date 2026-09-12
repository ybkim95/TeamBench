# Reference solution — GH1152_pymc_7575

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1152_pymc_7575`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1152_pymc_7575/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `pymc/logprob/scan.py` (modified, +4/-3)
- `tests/logprob/test_scan.py` (modified, +22/-0)

## Diff Summary (What the Fix Changes)

### `pymc/logprob/scan.py`
```diff
@@ -463,7 +463,9 @@ def find_measurable_scans(fgraph, node):
     # We must also replace any lingering references to the old RVs by the new measurable RVS
     # For example if we had measurable out1 = exp(normal()) and out2 = out1 - x
     # We need to replace references of original out1 by the new MeasurableExp(normal())
-    inner_outs = node.op.inner_outputs.copy()
+    clone_fgraph = node.op.fgraph.clone()
+    inner_inps = clone_fgraph.inputs
+    inner_outs = clone_fgraph.outputs
     inner_rvs_replacements = []
     for idx, new_inner_rv in zip(valued_output_idxs, inner_rvs, strict=True):
         old_inner_rv = inner_outs[idx]
@@ -474,8 +476,7 @@ def find_measurable_scans(fgraph, node):
         clone=False,
     )
     toposort_replace(temp_fgraph, inner_rvs_replacements)
-    inner_outs = temp_fgraph.outputs[: len(inner_outs)]
-    op = MeasurableScan(node.op.inner_inputs, inner_outs, node.op.info, mode=copy(node.op.mode))
+    op = MeasurableScan(inner_inps, inner_outs, node.op.info, mode=copy(node.op.mode))
     new_outs = op.make_node(*node.inputs).outputs
 
     old_outs = node.outputs
```

## Moved from `brief.md`

## Files That May Need Changes

- `pymc/logprob/scan.py`
