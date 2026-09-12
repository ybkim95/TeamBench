# Reference solution — GH1114_statsmodels_9739

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1114_statsmodels_9739`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1114_statsmodels_9739/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `statsmodels/formula/_manager.py` (modified, +2/-2)
- `statsmodels/formula/tests/test_formula.py` (modified, +13/-0)

## Diff Summary (What the Fix Changes)

### `statsmodels/formula/_manager.py`
```diff
@@ -474,11 +474,11 @@ def get_matrices(
                 or formula.strip().startswith("~")
             ):
                 output = patsy.dmatrix(
-                    formula, data, eval_env=eval_env, return_type=return_type, **kwargs
+                    formula, data, eval_env=_eval_env, return_type=return_type, **kwargs
                 )
             else:  # "~" in formula:
                 output = patsy.dmatrices(
-                    formula, data, eval_env=eval_env, return_type=return_type, **kwargs
+                    formula, data, eval_env=_eval_env, return_type=return_type, **kwargs
                 )
             if isinstance(output, tuple):
                 self._spec = output[1].design_info
```

## Moved from `brief.md`

## Files That May Need Changes

- `statsmodels/formula/_manager.py`
