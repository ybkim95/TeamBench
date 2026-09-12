# Reference solution — GH1155_matplotlib_30746

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1155_matplotlib_30746`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1155_matplotlib_30746/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `lib/matplotlib/backends/backend_pdf.py` (modified, +39/-0)
- `lib/matplotlib/tests/test_backend_pdf.py` (modified, +218/-0)

## Diff Summary (What the Fix Changes)

### `lib/matplotlib/backends/backend_pdf.py`
```diff
@@ -2104,11 +2104,28 @@ def draw_path_collection(self, gc, master_transform, paths, all_transforms,
 
         padding = np.max(linewidths)
         path_codes = []
+        path_extents = []
         for i, (path, transform) in enumerate(self._iter_collection_raw_paths(
                 master_transform, paths, all_transforms)):
             name = self.file.pathCollectionObject(
                 gc, path, transform, padding, filled, stroked)
             path_codes.append(name)
+            # Compute the extent of each marker path to enable per-marker
+            # bounds checking. This allows us to skip markers that are
+            # completely outside the visible canvas while preserving markers
+            # that are partially visible.
+            if len(path.vertices):
+                bbox = path.get_extents(transform)
+                # Store half-width and half-height for efficient bounds checking
+                path_extents.append((bbox.width / 2, bbox.height / 2))
+            else:
+                path_extents.append((0, 0))
+
+        # Create a mapping from path_id to extent for efficient lookup
+        path_extent_map = dict(zip(path_codes, path_extents))
+
+        canvas_width = self.file.width * 72
+        canvas_height = self.file.height * 72
 
         output = self.file.output
         output(*self.gc.push())
@@ -2118,6 +2135,28 @@ def draw_path_collection(self, gc, master_transform, paths, all_transforms,
                 facecolors, edgecolors, linewidths, linestyles,
                 antialiaseds, urls, offset_position, hatchcolors=hatchcolors):
 
+            # Optimization: Fast path for markers with centers inside canvas.
+            # This avoids the dictionary lookup for the common case where
+            # markers are visible, improving performance for large scatter plots.
+            if 0 <= xo <= canvas_width and 0 <= yo <= canvas_height:
+                # Marker center is inside canvas - definitely render it
+             
```

## Moved from `brief.md`

## Files That May Need Changes

- `lib/matplotlib/backends/backend_pdf.py`
