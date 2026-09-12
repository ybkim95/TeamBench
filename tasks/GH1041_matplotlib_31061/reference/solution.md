# Reference solution — GH1041_matplotlib_31061

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1041_matplotlib_31061`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1041_matplotlib_31061/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `lib/matplotlib/axes/_base.py` (modified, +14/-0)
- `lib/matplotlib/tests/test_text.py` (modified, +12/-0)
- `lib/matplotlib/text.py` (modified, +9/-0)

## Diff Summary (What the Fix Changes)

### `lib/matplotlib/axes/_base.py`
```diff
@@ -2443,6 +2443,20 @@ def _add_text(self, txt):
         self.stale = True
         return txt
 
+    def _point_in_data_domain(self, x, y):
+        """
+        Check if the data point (x, y) is within the valid domain of the axes
+        scales.
+
+        Returns False if the point is outside the data range
+        (e.g. negative coordinates with a log scale).
+        """
+        for val, axis in zip([x, y], self._axis_map.values()):
+            vmin, vmax = axis.limit_range_for_scale(val, val)
+            if vmin != val or vmax != val:
+                return False
+        return True
+
     def _update_line_limits(self, line):
         """
         Figures out the data limit of the given line, updating `.Axes.dataLim`.
```

### `lib/matplotlib/text.py`
```diff
@@ -1060,6 +1060,15 @@ def get_window_extent(self, renderer=None, dpi=None):
             bbox = bbox.translated(x, y)
             return bbox
 
+    def get_tightbbox(self, renderer=None):
+        # Exclude text at data coordinates outside the valid domain of the axes
+        # scales (e.g., negative coordinates with a log scale).
+        if (self.axes
+                and self.get_transform() == self.axes.transData
+                and not self.axes._point_in_data_domain(*self.get_unitless_position())):
+            return Bbox.null()
+        return super().get_tightbbox(renderer)
+
     def set_backgroundcolor(self, color):
         """
         Set the background color of the text.
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `lib/matplotlib/axes/_base.py`
- `lib/matplotlib/text.py`
