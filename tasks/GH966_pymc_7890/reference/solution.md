# Reference solution — GH966_pymc_7890

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH966_pymc_7890`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH966_pymc_7890/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `pymc/sampling/forward.py` (modified, +4/-7)
- `tests/sampling/test_forward.py` (modified, +30/-0)

## Diff Summary (What the Fix Changes)

### `pymc/sampling/forward.py`
```diff
@@ -1059,14 +1059,11 @@ def vectorize_over_posterior(
         for rv in general_toposort(  # type: ignore[call-overload]
             all_rvs, lambda x: x.owner.inputs if x.owner is not None else None
         )
-        if rv in all_rvs
+        if rv in all_rvs and rv not in needed_rvs
     ]:
-        rv_ancestors = ancestors([rv], blockers=[*needed_rvs, *independent_rvs, *outputs])
-        if (
-            rv not in needed_rvs
-            and not ({*outputs, *independent_rvs} & set(rv_ancestors))
-            and {var for var in rv_ancestors if var in all_rvs} <= {rv, *needed_rvs}
-        ):
+        blockers = [*needed_rvs, *independent_rvs, *outputs]
+        rv_ancestors = ancestors([rv], blockers=blockers)
+        if not (set(blockers) & set(rv_ancestors)):
             independent_rvs.append(rv)
     for rv in independent_rvs:
         replace_dict[rv] = change_dist_size(rv, new_size=batch_shape, expand=True)
```

## Moved from `brief.md`

## Files That May Need Changes

- `pymc/sampling/forward.py`
