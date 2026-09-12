# Reference solution — GH1154_matplotlib_30795

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1154_matplotlib_30795`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1154_matplotlib_30795/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/api/next_api_changes/behavior/28437-CH.rst` (modified, +7/-4)
- `lib/matplotlib/image.py` (modified, +4/-2)
- `lib/matplotlib/tests/test_image.py` (modified, +4/-3)

## Diff Summary (What the Fix Changes)

### `lib/matplotlib/image.py`
```diff
@@ -512,8 +512,10 @@ def _make_image(self, A, in_bbox, out_bbox, clip_bbox, magnification=1.0,
                     if A.shape[2] == 3:  # image has no alpha channel
                         A = np.dstack([A, np.ones(A.shape[:2])])
                 elif np.ndim(alpha) > 0:  # Array alpha
-                    # user-specified array alpha overrides the existing alpha channel
-                    A = np.dstack([A[..., :3], alpha])
+                    if A.shape[2] == 3:  # RGB: use array alpha directly
+                        A = np.dstack([A, alpha])
+                    else:  # RGBA: multiply existing alpha by array alpha
+                        A = np.dstack([A[..., :3], A[..., 3] * alpha])
                 else:  # Scalar alpha
                     if A.shape[2] == 3:  # broadcast scalar alpha
                         A = np.dstack([A, np.full(A.shape[:2], alpha, np.float32)])
```

## Moved from `brief.md`

## Files That May Need Changes

- `lib/matplotlib/image.py`

## Reference patch found inline in the issue text

```diff
diff --git a/lib/matplotlib/image.py b/lib/matplotlib/image.py
index 135934a244..0ca26bdabf 100644
--- a/lib/matplotlib/image.py
+++ b/lib/matplotlib/image.py
@@ -553,9 +553,11 @@ class _ImageBase(martist.Artist, cm.ScalarMappable):
             else:
                 if A.ndim == 2:  # _interpolation_stage == 'rgba'
                     self.norm.autoscale_None(A)
-                    A = self.to_rgba(A)
-                if A.shape[2] == 3:
+                    A = self.to_rgba(A, alpha=self.get_alpha())
+                elif A.shape[2] == 3:
                     A = _rgb_to_rgba(A)
+                    if alpha := self.get_alpha() is not None:
+                        A[:, :, 3] = self.get_alpha()
                 alpha = self._get_scalar_alpha()
                 output_alpha = _resample(  # resample alpha channel
                     self, A[..., 3], out_shape, t, alpha=alpha)
```
