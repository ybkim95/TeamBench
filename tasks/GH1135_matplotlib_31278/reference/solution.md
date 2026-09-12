# Reference solution — GH1135_matplotlib_31278

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1135_matplotlib_31278`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1135_matplotlib_31278/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `lib/matplotlib/contour.py` (modified, +2/-0)
- `lib/matplotlib/tests/test_datetime.py` (modified, +13/-2)

## Diff Summary (What the Fix Changes)

### `lib/matplotlib/contour.py`
```diff
@@ -451,6 +451,8 @@ def add_label_near(self, x, y, inline=True, inline_spacing=5,
         if transform is None:
             transform = self.axes.transData
         if transform:
+            x = self.axes.convert_xunits(x)
+            y = self.axes.convert_yunits(y)
             x, y = transform.transform((x, y))
 
         idx_level_min, idx_vtx_min, proj = self._find_nearest_contour(
```

## Moved from `brief.md`

## Files That May Need Changes

- `lib/matplotlib/contour.py`
