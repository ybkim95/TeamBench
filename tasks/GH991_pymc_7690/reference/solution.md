# Reference solution — GH991_pymc_7690

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH991_pymc_7690`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH991_pymc_7690/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `pymc/distributions/distribution.py` (modified, +4/-2)
- `tests/distributions/test_custom.py` (modified, +71/-2)

## Diff Summary (What the Fix Changes)

### `pymc/distributions/distribution.py`
```diff
@@ -27,7 +27,7 @@
 
 from pytensor import tensor as pt
 from pytensor.compile.builders import OpFromGraph
-from pytensor.graph import FunctionGraph, clone_replace, node_rewriter
+from pytensor.graph import FunctionGraph, graph_replace, node_rewriter
 from pytensor.graph.basic import Apply, Variable
 from pytensor.graph.rewriting.basic import in2out
 from pytensor.graph.utils import MetaType
@@ -588,7 +588,9 @@ def inline_symbolic_random_variable(fgraph, node):
     """Expand a SymbolicRV when obtaining the logp graph if `inline_logprob` is True."""
     op = node.op
     if op.inline_logprob:
-        return clone_replace(op.inner_outputs, dict(zip(op.inner_inputs, node.inputs)))
+        return graph_replace(
+            op.inner_outputs, dict(zip(op.inner_inputs, node.inputs)), strict=False
+        )
 
 
 # Registered before pre-canonicalization which happens at position=-10
```

## Moved from `brief.md`

## Files That May Need Changes

- `pymc/distributions/distribution.py`
