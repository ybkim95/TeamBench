# Reference solution — GH1060_ultralytics_23903

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1060_ultralytics_23903`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1060_ultralytics_23903/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `tests/test_python.py` (modified, +1/-5)
- `ultralytics/data/base.py` (modified, +5/-1)
- `ultralytics/data/utils.py` (modified, +7/-3)
- `ultralytics/utils/metrics.py` (modified, +1/-1)

## Diff Summary (What the Fix Changes)

### `ultralytics/data/base.py`
```diff
@@ -280,7 +280,11 @@ def cache_images_to_disk(self, i: int) -> None:
         """Save an image as an *.npy file for faster loading."""
         f = self.npy_files[i]
         if not f.exists():
-            np.save(f.as_posix(), imread(self.im_files[i], flags=self.cv2_flag), allow_pickle=False)
+            try:
+                np.save(f.as_posix(), imread(self.im_files[i], flags=self.cv2_flag), allow_pickle=False)
+            except Exception as e:
+                f.unlink(missing_ok=True)
+                LOGGER.warning(f"{self.prefix}WARNING ⚠️ Failed to cache image {f}: {e}")
 
     def check_cache_disk(self, safety_margin: float = 0.5) -> bool:
         """Check if there's enough disk space for caching images.
```

### `ultralytics/data/utils.py`
```diff
@@ -806,8 +806,12 @@ def save_dataset_cache_file(prefix: str, path: Path, x: dict, version: str):
     if is_dir_writeable(path.parent):
         if path.exists():
             path.unlink()  # remove *.cache file if exists
-        with open(str(path), "wb") as file:  # context manager here fixes windows async np.save bug
-            np.save(file, x)
-        LOGGER.info(f"{prefix}New cache created: {path}")
+        try:
+            with open(str(path), "wb") as file:  # context manager here fixes windows async np.save bug
+                np.save(file, x)
+            LOGGER.info(f"{prefix}New cache created: {path}")
+        except Exception as e:
+            Path(path).unlink(missing_ok=True)  # remove partially written file
+            LOGGER.warning(f"{prefix}WARNING ⚠️ Failed to save cache to {path}: {e}")
     else:
         LOGGER.warning(f"{prefix}Cache directory {path.parent} is not writable, cache not saved.")
```

### `ultralytics/utils/metrics.py`
```diff
@@ -962,7 +962,7 @@ def maps(self) -> np.ndarray:
     def fitness(self) -> float:
         """Return model fitness as a weighted combination of metrics."""
         w = [0.0, 0.0, 0.0, 1.0]  # weights for [P, R, mAP@0.5, mAP@0.5:0.95]
-        return (np.nan_to_num(np.array(self.mean_results())) * w).sum()
+        return float((np.nan_to_num(np.array(self.mean_results())) * w).sum())
 
     def update(self, results: tuple):
         """Update the evaluation metrics with a new set of results.
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `ultralytics/data/base.py`
- `ultralytics/data/utils.py`
- `ultralytics/utils/metrics.py`
