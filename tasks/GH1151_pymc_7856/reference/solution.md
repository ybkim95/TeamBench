# Reference solution — GH1151_pymc_7856

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1151_pymc_7856`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1151_pymc_7856/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `pymc/backends/arviz.py` (modified, +3/-1)
- `tests/backends/test_arviz.py` (modified, +11/-0)

## Diff Summary (What the Fix Changes)

### `pymc/backends/arviz.py`
```diff
@@ -618,11 +618,13 @@ def dataset_to_point_list(
     for vn in var_names:
         if not isinstance(vn, str):
             raise ValueError(f"Variable names must be str, but dataset key {vn} is a {type(vn)}.")
+
     num_sample_dims = len(sample_dims)
     stacked_dims = {dim_name: ds[var_names[0]][dim_name] for dim_name in sample_dims}
     transposed_dict = {vn: da.transpose(*sample_dims, ...) for vn, da in ds.items()}
+    stacked_size = np.prod(transposed_dict[var_names[0]].shape[:num_sample_dims], dtype=int)
     stacked_dict = {
-        vn: da.values.reshape((-1, *da.shape[num_sample_dims:]))
+        vn: da.values.reshape((stacked_size, *da.shape[num_sample_dims:]))
         for vn, da in transposed_dict.items()
     }
     points = [
```

## Moved from `brief.md`

## Files That May Need Changes

- `pymc/backends/arviz.py`
