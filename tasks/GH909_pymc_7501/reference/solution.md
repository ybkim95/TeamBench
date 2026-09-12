# Reference solution — GH909_pymc_7501

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH909_pymc_7501`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH909_pymc_7501/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `pymc/printing.py` (modified, +11/-0)
- `tests/test_printing.py` (modified, +27/-7)

## Diff Summary (What the Fix Changes)

### `pymc/printing.py`
```diff
@@ -13,6 +13,8 @@
 #   limitations under the License.
 
 
+import re
+
 from functools import partial
 
 from pytensor.compile import SharedVariable
@@ -58,6 +60,7 @@ def str_for_dist(
     if "latex" in formatting:
         if print_name is not None:
             print_name = r"\text{" + _latex_escape(print_name.strip("$")) + "}"
+            print_name = _format_underscore(print_name)
 
         op_name = (
             dist.owner.op._print_name[1]
@@ -114,6 +117,7 @@ def str_for_model(model: Model, formatting: str = "plain", include_params: bool
     if not var_reprs:
         return ""
     if "latex" in formatting:
+        var_reprs = [_format_underscore(x) for x in var_reprs]
         var_reprs = [
             var_repr.replace(r"\sim", r"&\sim &").strip("$")
             for var_repr in var_reprs
@@ -295,3 +299,10 @@ def _default_repr_pretty(obj: TensorVariable | Model, p, cycle):
 except (ModuleNotFoundError, AttributeError):
     # no ipython shell
     pass
+
+
+def _format_underscore(variable: str) -> str:
+    """
+    Escapes all unescaped underscores in the variable name for LaTeX representation.
+    """
+    return re.sub(r"(?<!\\)_", r"\\_", variable)
```

## Moved from `brief.md`

## Files That May Need Changes

- `pymc/printing.py`
