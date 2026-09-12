# Reference solution — GH1086_matplotlib_31133

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1086_matplotlib_31133`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1086_matplotlib_31133/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `lib/matplotlib/backends/_backend_tk.py` (modified, +14/-4)
- `lib/matplotlib/tests/test_backend_tk.py` (modified, +50/-0)

## Diff Summary (What the Fix Changes)

### `lib/matplotlib/backends/_backend_tk.py`
```diff
@@ -270,14 +270,24 @@ def _update_device_pixel_ratio(self, event=None):
         elif sys.platform == "linux":
             ratio = self._tkcanvas.winfo_fpixels('1i') / 96
         if ratio is not None and self._set_device_pixel_ratio(ratio):
-            # The easiest way to resize the canvas is to resize the canvas
-            # widget itself, since we implement all the logic for resizing the
-            # canvas backing store on that event.
+            # Resize the canvas widget, then explicitly update the figure
+            # size to match the actual widget dimensions.  When the canvas
+            # is constrained by a geometry manager (pack/grid), <Configure>
+            # may not fire after configure(), so we handle the resize
+            # directly — similar to Qt's _update_pixel_ratio approach.
             w, h = self.get_width_height(physical=True)
             self._tkcanvas.configure(width=w, height=h)
+            self._resize_figure_for_canvas_size(
+                self._tkcanvas.winfo_width(),
+                self._tkcanvas.winfo_height())
 
     def resize(self, event):
-        width, height = event.width, event.height
+        self._resize_figure_for_canvas_size(event.width, event.height)
+
+    def _resize_figure_for_canvas_size(self, width, height):
+        """Update figure size and redraw based on a given canvas size."""
+        if width <= 0 or height <= 0:
+            return
 
         # compute desired figure size in inches
         dpival = self.figure.dpi
```

## Moved from `brief.md`

## Files That May Need Changes

- `lib/matplotlib/backends/_backend_tk.py`
