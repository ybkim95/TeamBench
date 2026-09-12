# Reference solution — GH1036_FLAML_1405

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1036_FLAML_1405`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1036_FLAML_1405/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `flaml/automl/task/generic_task.py` (modified, +3/-3)
- `test/automl/test_split.py` (modified, +38/-2)

## Diff Summary (What the Fix Changes)

### `flaml/automl/task/generic_task.py`
```diff
@@ -769,10 +769,10 @@ def evaluate_model_CV(
             if not is_spark_dataframe:
                 y_train, y_val = y_train_split[train_index], y_train_split[val_index]
                 if weight is not None:
-                    fit_kwargs["sample_weight"], weight_val = (
-                        weight[train_index],
-                        weight[val_index],
+                    fit_kwargs["sample_weight"] = (
+                        weight[train_index] if isinstance(weight, np.ndarray) else weight.iloc[train_index]
                     )
+                    weight_val = weight[val_index] if isinstance(weight, np.ndarray) else weight.iloc[val_index]
                 if groups is not None:
                     fit_kwargs["groups"] = (
                         groups[train_index] if isinstance(groups, np.ndarray) else groups.iloc[train_index]
```

## Moved from `brief.md`

## Files That May Need Changes

- `flaml/automl/task/generic_task.py`
