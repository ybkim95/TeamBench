# Reference solution — GH1085_matplotlib_31313

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1085_matplotlib_31313`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1085_matplotlib_31313/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `lib/matplotlib/image.py` (modified, +15/-7)
- `lib/matplotlib/tests/baseline_images/test_axes/specgram_magnitude_freqs.png` (modified, +0/-0)
- `lib/matplotlib/tests/baseline_images/test_axes/specgram_magnitude_freqs_linear.png` (modified, +0/-0)
- `lib/matplotlib/tests/baseline_images/test_image/alignment_half_display_pixels.png` (added, +0/-0)
- `lib/matplotlib/tests/baseline_images/test_image/image_bounds_handling.png` (modified, +0/-0)
- `lib/matplotlib/tests/test_image.py` (modified, +60/-0)
- `lib/mpl_toolkits/axes_grid1/tests/baseline_images/test_axes_grid1/imagegrid_cbar_mode.png` (modified, +0/-0)
- `src/_image_resample.h` (modified, +12/-6)
- `src/agg_workaround.h` (modified, +15/-6)

## Diff Summary (What the Fix Changes)

### `lib/matplotlib/image.py`
```diff
@@ -209,9 +209,15 @@ def _resample(
 
     # When an output pixel falls exactly on the edge between two input pixels, the Agg
     # resampler will use the right input pixel as the nearest neighbor.  We want the
-    # left input pixel to be chosen instead, so we flip the supplied transform.
+    # left input pixel to be chosen instead, so we flip the input data and the supplied
+    # transform.  If origin != 'upper', the transform will already include a flip in the
+    # vertical direction.
     if interpolation == 'nearest':
-        transform += Affine2D().translate(-out.shape[1], -out.shape[0]).scale(-1, -1)
+        transform = Affine2D().translate(-data.shape[1], 0).scale(-1, 1) + transform
+        data = np.flip(data, axis=1)
+        if image_obj.origin == 'upper':
+            transform = Affine2D().translate(0, -data.shape[0]).scale(1, -1) + transform
+            data = np.flip(data, axis=0)
 
     _image.resample(data, out, transform,
                     _interpd_[interpolation],
@@ -220,10 +226,6 @@ def _resample(
                     image_obj.get_filternorm(),
                     image_obj.get_filterrad())
 
-    # Because we flipped the supplied transform, we then flip the output image back.
-    if interpolation == 'nearest':
-        out = np.flip(out, axis=(0, 1))
-
     return out
 
 
@@ -408,7 +410,13 @@ def _make_image(self, A, in_bbox, out_bbox, clip_bbox, magnification=1.0,
         magnified_extents = clipped_bbox.extents * magnification
         if ((not unsampled) and round_to_pixel_border):
             # Round to the nearest output pixel
-            magnified_bbox = Bbox.from_extents((magnified_extents + 0.5).astype(int))
+            # Add a tiny fudge amount to account for numerical precision loss
+            # on the two sides away from the Agg anchor point (x0, y1)
+            x0 = np.floor(magnified_extents[0] + 0.5)  # round half up
+            y0 = np.ceil(magnified_extents[1] - 0.5 - 1e-8)  # round half down
+           
```

## Moved from `brief.md`

## Files That May Need Changes

- `lib/matplotlib/image.py`
