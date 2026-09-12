# Reference solution — GH1104_matplotlib_31128

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1104_matplotlib_31128`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1104_matplotlib_31128/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `lib/matplotlib/axes/_base.py` (modified, +9/-0)
- `lib/matplotlib/tests/test_axes.py` (modified, +24/-0)

## Diff Summary (What the Fix Changes)

### `lib/matplotlib/axes/_base.py`
```diff
@@ -29,6 +29,7 @@
 import matplotlib.text as mtext
 import matplotlib.ticker as mticker
 import matplotlib.transforms as mtransforms
+import matplotlib.collections as mcollections
 
 _log = logging.getLogger(__name__)
 
@@ -2415,6 +2416,12 @@ def _update_image_limits(self, image):
         xmin, xmax, ymin, ymax = image.get_extent()
         self.axes.update_datalim(((xmin, ymin), (xmax, ymax)))
 
+    def _update_collection_limits(self, collection):
+     offsets = collection.get_offsets()
+     if offsets is not None and len(offsets):
+        self.update_datalim(offsets)
+
+
     def add_line(self, line):
         """
         Add a `.Line2D` to the Axes; return the line.
@@ -2605,6 +2612,8 @@ def relim(self, visible_only=False):
                     self._update_patch_limits(artist)
                 elif isinstance(artist, mimage.AxesImage):
                     self._update_image_limits(artist)
+                elif isinstance(artist, mcollections.Collection):
+                 self._update_collection_limits(artist)
 
     def update_datalim(self, xys, updatex=True, updatey=True):
         """
```

## Moved from `brief.md`

## Files That May Need Changes

- `lib/matplotlib/axes/_base.py`
