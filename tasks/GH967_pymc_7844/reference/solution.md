# Reference solution — GH967_pymc_7844

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH967_pymc_7844`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH967_pymc_7844/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `pymc/model/core.py` (modified, +4/-1)
- `pymc/model_graph.py` (modified, +42/-64)
- `scripts/run_mypy.py` (modified, +1/-1)
- `tests/model/test_core.py` (modified, +1/-1)
- `tests/test_model_graph.py` (modified, +27/-2)

## Diff Summary (What the Fix Changes)

### `pymc/model/core.py`
```diff
@@ -52,7 +52,6 @@
 from pymc.logprob.basic import transformed_conditional_logp
 from pymc.logprob.transforms import Transform
 from pymc.logprob.utils import ParameterValueError, replace_rvs_by_values
-from pymc.model_graph import model_to_graphviz, model_to_mermaid
 from pymc.pytensorf import (
     PointFunc,
     SeedSequenceSeed,
@@ -440,6 +439,8 @@ def __exit__(self, exc_type: None, exc_val: None, exc_tb: None) -> None:
     def _display_(self):
         import marimo as mo
 
+        from pymc.model_graph import model_to_mermaid
+
         return mo.mermaid(model_to_mermaid(self))
 
     @staticmethod
@@ -2002,6 +2003,8 @@ def to_graphviz(
             # creates the file `schools.pdf`
             schools.to_graphviz().render("schools")
         """
+        from pymc.model_graph import model_to_graphviz
+
         return model_to_graphviz(
             model=self,
             var_names=var_names,
```

### `pymc/model_graph.py`
```diff
@@ -21,16 +21,11 @@
 from typing import Any, cast
 
 from pytensor import function
-from pytensor.graph import Apply
 from pytensor.graph.basic import ancestors, walk
-from pytensor.scalar.basic import Cast
-from pytensor.tensor.elemwise import Elemwise
-from pytensor.tensor.random.op import RandomVariable
 from pytensor.tensor.shape import Shape
 from pytensor.tensor.variable import TensorVariable
 
-import pymc as pm
-
+from pymc.model.core import modelcontext
 from pymc.util import VarName, get_default_varnames, get_var_name
 
 __all__ = (
@@ -241,42 +236,32 @@ class ModelGraph:
     def __init__(self, model):
         self.model = model
         self._all_var_names = get_default_varnames(self.model.named_vars, include_transformed=False)
+        self._all_vars = {model[var_name] for var_name in self._all_var_names}
         self.var_list = self.model.named_vars.values()
 
     def get_parent_names(self, var: TensorVariable) -> set[VarName]:
-        if var.owner is None or var.owner.inputs is None:
+        if var.owner is None:
             return set()
 
-        def _filter_non_parameter_inputs(var):
-            node = var.owner
-            if isinstance(node.op, Shape):
-                # Don't show shape-related dependencies
-                return []
-            if isinstance(node.op, RandomVariable):
-                # Filter out rng and size parameters or RandomVariable nodes
-                return node.op.dist_params(node)
-            else:
-                # Otherwise return all inputs
-                return node.inputs
-
-        blockers = set(self.model.named_vars)
+        named_vars = self._all_vars
 
         def _expand(x):
-            nonlocal blockers
-            if x.name in blockers:
+            if x in named_vars:
+                # Don't go beyond named_vars
                 return [x]
-            if isinstance(x.owner, Apply):
-                return reversed(_filter_non_parameter_inputs(x))
-            return []
-
-        par
```

### `scripts/run_mypy.py`
```diff
@@ -168,7 +168,7 @@ def check_no_unexpected_results(mypy_lines: Iterator[str]):
         for section, sdf in df.reset_index().groupby(args.groupby):
             print(f"\n\n[{section}]")
             for row in sdf.itertuples():
-                print(f"{row.file}:{row.line}: {row.type}: {row.message}")
+                print(f"{row.file}:{row.line}: {row.type} [{row.errorcode}]: {row.message}")
         print()
     else:
         print(
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `pymc/model/core.py`
- `pymc/model_graph.py`
- `scripts/run_mypy.py`
