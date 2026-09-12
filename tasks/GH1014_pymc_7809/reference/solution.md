# Reference solution — GH1014_pymc_7809

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1014_pymc_7809`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1014_pymc_7809/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `pymc/model/core.py` (modified, +1/-0)
- `tests/model/test_core.py` (modified, +14/-0)

## Diff Summary (What the Fix Changes)

### `pymc/model/core.py`
```diff
@@ -964,6 +964,7 @@ def add_coord(
         if name in self.coords:
             if not np.array_equal(values, self.coords[name]):
                 raise ValueError(f"Duplicate and incompatible coordinate: {name}.")
+            return
         if length is not None and not isinstance(length, int | Variable):
             raise ValueError(
                 f"The `length` passed for the '{name}' coord must be an int, PyTensor Variable or None."
```

## Moved from `brief.md`

## Files That May Need Changes

- `pymc/model/core.py`
