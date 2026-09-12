# Reference solution — GH1157_matplotlib_30752

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1157_matplotlib_30752`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1157_matplotlib_30752/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `lib/matplotlib/axes/_axes.py` (modified, +17/-2)
- `lib/matplotlib/tests/test_axes.py` (modified, +79/-0)

## Diff Summary (What the Fix Changes)

### `lib/matplotlib/axes/_axes.py`
```diff
@@ -2,6 +2,7 @@
 import itertools
 import logging
 import math
+import datetime
 from numbers import Integral, Number, Real
 
 import re
@@ -9050,14 +9051,28 @@ def violin(self, vpstats, positions=None, vert=None,
             positions = range(1, N + 1)
         elif len(positions) != N:
             raise ValueError(datashape_message.format("positions"))
-
         # Validate widths
         if np.isscalar(widths):
             widths = [widths] * N
         elif len(widths) != N:
             raise ValueError(datashape_message.format("widths"))
 
-        # Validate side
+        # For usability / better error message:
+        # Validate that datetime-like positions have timedelta-like widths.
+        # Checking only the first element is good enough for standard misuse cases
+        if N > 0:  # No need to validate if there is no data
+            pos0 = positions[0]
+            width0 = widths[0]
+            if (isinstance(pos0, (datetime.datetime, datetime.date))
+                and not isinstance(width0, datetime.timedelta)):
+                raise TypeError(
+                    "datetime/date 'position' values require timedelta 'widths'. "
+                    "For example, use positions=[datetime.date(2024, 1, 1)] "
+                    "and widths=[datetime.timedelta(days=1)].")
+            elif (isinstance(pos0, np.datetime64)
+                and not isinstance(width0, np.timedelta64)):
+                raise TypeError(
+                    "np.datetime64 'position' values require np.timedelta64 'widths'")
         _api.check_in_list(["both", "low", "high"], side=side)
 
         # Calculate ranges for statistics lines (shape (2, N)).
```

## Moved from `brief.md`

## Files That May Need Changes

- `lib/matplotlib/axes/_axes.py`
