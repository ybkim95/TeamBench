# Reference solution — GH1105_matplotlib_31203

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1105_matplotlib_31203`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1105_matplotlib_31203/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `lib/matplotlib/axes/_axes.py` (modified, +9/-0)
- `lib/matplotlib/tests/test_axes.py` (modified, +15/-0)

## Diff Summary (What the Fix Changes)

### `lib/matplotlib/axes/_axes.py`
```diff
@@ -7418,6 +7418,15 @@ def hist(self, x, bins=None, range=None, density=False, weights=None,
         x = cbook._reshape_2D(x, 'x')
         nx = len(x)  # number of datasets
 
+        for arr in x:
+            if len(arr) > 0 and isinstance(
+                arr[0], (datetime.timedelta, np.timedelta64)
+            ):
+                raise TypeError(
+                    "Axes.hist does not currently support timedelta inputs. "
+                    "Convert to numeric values  (e.g., .total_seconds()) first."
+                )
+
         # Process unit information.  _process_unit_info sets the unit and
         # converts the first dataset; then we convert each following dataset
         # one at a time.
```

## Moved from `brief.md`

## Files That May Need Changes

- `lib/matplotlib/axes/_axes.py`
