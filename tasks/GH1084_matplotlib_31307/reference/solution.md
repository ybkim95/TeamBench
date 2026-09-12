# Reference solution — GH1084_matplotlib_31307

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1084_matplotlib_31307`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1084_matplotlib_31307/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `lib/matplotlib/lines.py` (modified, +9/-3)
- `lib/matplotlib/patches.py` (modified, +7/-3)
- `lib/matplotlib/tests/test_axes.py` (modified, +7/-3)
- `lib/matplotlib/tests/test_lines.py` (modified, +7/-0)
- `lib/matplotlib/tests/test_patches.py` (modified, +8/-0)

## Diff Summary (What the Fix Changes)

### `lib/matplotlib/lines.py`
```diff
@@ -798,8 +798,11 @@ def draw(self, renderer):
                 if self.get_sketch_params() is not None:
                     gc.set_sketch_params(*self.get_sketch_params())
 
-                # We first draw a path within the gaps if needed.
-                if self.is_dashed() and self._gapcolor is not None:
+                # We first draw a path within the gaps if needed, but only for
+                # visible dashed lines; zero-width lines would otherwise yield
+                # all-zero dashes.
+                if (self._linewidth > 0 and self.is_dashed()
+                        and self._gapcolor is not None):
                     lc_rgba = mcolors.to_rgba(self._gapcolor, self._alpha)
                     gc.set_foreground(lc_rgba, isRGBA=True)
 
@@ -812,7 +815,10 @@ def draw(self, renderer):
                 lc_rgba = mcolors.to_rgba(self._color, self._alpha)
                 gc.set_foreground(lc_rgba, isRGBA=True)
 
-                gc.set_dashes(*self._dash_pattern)
+                if self._linewidth > 0:
+                    gc.set_dashes(*self._dash_pattern)
+                else:
+                    gc.set_dashes(0, None)
                 renderer.draw_path(gc, tpath, affine.frozen())
                 gc.restore()
 
```

### `lib/matplotlib/patches.py`
```diff
@@ -709,8 +709,9 @@ def _draw_paths_with_artist_properties(
             from matplotlib.patheffects import PathEffectRenderer
             renderer = PathEffectRenderer(self.get_path_effects(), renderer)
 
-        # Draw the gaps first if gapcolor is set
-        if self._has_dashed_edge() and self._gapcolor is not None:
+        # We first draw a path within the gaps if needed, but only for visible
+        # dashed edges; zero-width edges would otherwise yield all-zero dashes.
+        if lw > 0 and self._has_dashed_edge() and self._gapcolor is not None:
             gc.set_foreground(self._gapcolor, isRGBA=True)
             offset_gaps, gaps = mlines._get_inverse_dash_pattern(
                 *self._dash_pattern)
@@ -720,7 +721,10 @@ def _draw_paths_with_artist_properties(
 
         # Draw the main edge
         gc.set_foreground(self._edgecolor, isRGBA=True)
-        gc.set_dashes(*self._dash_pattern)
+        if lw > 0:
+            gc.set_dashes(*self._dash_pattern)
+        else:
+            gc.set_dashes(0, None)
         for draw_path_args in draw_path_args_list:
             renderer.draw_path(gc, *draw_path_args)
 
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `lib/matplotlib/lines.py`
- `lib/matplotlib/patches.py`
