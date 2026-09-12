# Reference solution — GH1156_matplotlib_31031

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1156_matplotlib_31031`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1156_matplotlib_31031/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `lib/matplotlib/tests/test_widgets.py` (modified, +19/-0)
- `lib/matplotlib/widgets.py` (modified, +3/-3)

## Diff Summary (What the Fix Changes)

### `lib/matplotlib/widgets.py`
```diff
@@ -1110,11 +1110,11 @@ def _clicked(self, event):
         if self.ignore(event) or event.button != 1 or not self.ax.contains(event)[0]:
             return
         idxs = [  # Indices of frames and of texts that contain the event.
-            *self._frames.contains(event)[1]["ind"],
+            *self._buttons.contains(event)[1]["ind"],
             *[i for i, text in enumerate(self.labels) if text.contains(event)[0]]]
         if idxs:
-            coords = self._frames.get_offset_transform().transform(
-                self._frames.get_offsets())
+            coords = self._buttons.get_offset_transform().transform(
+                self._buttons.get_offsets())
             self.set_active(  # Closest index, only looking in idxs.
                 idxs[(((event.x, event.y) - coords[idxs]) ** 2).sum(-1).argmin()])
 
```

## Moved from `brief.md`

## Files That May Need Changes

- `lib/matplotlib/widgets.py`
