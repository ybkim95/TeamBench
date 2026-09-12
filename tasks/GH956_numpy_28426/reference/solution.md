# Reference solution — GH956_numpy_28426

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH956_numpy_28426`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH956_numpy_28426/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/release/upcoming_changes/28426.change.rst` (added, +6/-0)
- `numpy/lib/_histograms_impl.py` (modified, +9/-15)
- `numpy/lib/tests/test_histograms.py` (modified, +11/-3)

## Diff Summary (What the Fix Changes)

### `numpy/lib/_histograms_impl.py`
```diff
@@ -228,28 +228,24 @@ def _hist_bin_fd(x, range):
 
 def _hist_bin_auto(x, range):
     """
-    Histogram bin estimator that uses the minimum width of the
-    Freedman-Diaconis and Sturges estimators if the FD bin width is non-zero.
-    If the bin width from the FD estimator is 0, the Sturges estimator is used.
+    Histogram bin estimator that uses the minimum width of a relaxed
+    Freedman-Diaconis and Sturges estimators if the FD bin width does
+    not result in a large number of bins. The relaxed Freedman-Diaconis estimator
+    limits the bin width to half the sqrt estimated to avoid small bins.
 
     The FD estimator is usually the most robust method, but its width
     estimate tends to be too large for small `x` and bad for data with limited
     variance. The Sturges estimator is quite good for small (<1000) datasets
     and is the default in the R language. This method gives good off-the-shelf
     behaviour.
 
-    If there is limited variance the IQR can be 0, which results in the
-    FD bin width being 0 too. This is not a valid bin width, so
-    ``np.histogram_bin_edges`` chooses 1 bin instead, which may not be optimal.
-    If the IQR is 0, it's unlikely any variance-based estimators will be of
-    use, so we revert to the Sturges estimator, which only uses the size of the
-    dataset in its calculation.
 
     Parameters
     ----------
     x : array_like
         Input data that is to be histogrammed, trimmed to range. May not
         be empty.
+    range : Tuple with range for the histogram
 
     Returns
     -------
@@ -261,12 +257,10 @@ def _hist_bin_auto(x, range):
     """
     fd_bw = _hist_bin_fd(x, range)
     sturges_bw = _hist_bin_sturges(x, range)
-    del range  # unused
-    if fd_bw:
-        return min(fd_bw, sturges_bw)
-    else:
-        # limited variance, so we return a len dependent bw estimator
-        return sturges_bw
+    sqrt_bw = _hist_bin_sqrt(x, range)
+    # heuristic to limit the maximal number of bins

```

## Moved from `brief.md`

## Files That May Need Changes

- `numpy/lib/_histograms_impl.py`
