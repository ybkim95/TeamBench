# Reference solution — GH891_statsmodels_9487

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH891_statsmodels_9487`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH891_statsmodels_9487/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `statsmodels/sandbox/stats/multicomp.py` (modified, +131/-26)
- `statsmodels/stats/multicomp.py` (modified, +22/-4)
- `statsmodels/stats/tests/test_pairwise.py` (modified, +65/-3)

## Diff Summary (What the Fix Changes)

### `statsmodels/sandbox/stats/multicomp.py`
```diff
@@ -71,6 +71,7 @@
 import numpy as np
 from numpy.testing import assert_almost_equal, assert_equal
 from scipy import interpolate, stats
+import pandas as pd
 
 from statsmodels.graphics import utils
 from statsmodels.iolib.table import SimpleTable
@@ -646,6 +647,9 @@ def __init__(
         reject2=None,
         variance=None,
         pvalues=None,
+        alpha=None,
+        group_t=None,
+        group_c=None,
     ):
         self._multicomp = mc_object
         self._results_table = results_table
@@ -658,22 +662,85 @@ def __init__(
         self.reject2 = reject2
         self.variance = variance
         self.pvalues = pvalues
+        self.alpha = alpha
+        self.group_t = group_t
+        self.group_c = group_c
         # Taken out of _multicomp for ease of access for unknowledgeable users
         self.data = self._multicomp.data
         self.groups = self._multicomp.groups
         self.groupsunique = self._multicomp.groupsunique
 
+        if np.size(df_total) > 1:  # or should it be np.isscalar
+            # assume we have Games-Howell, unequal var case
+            self._qcrit_hsd = None
+        else:
+            self._qcrit_hsd = q_crit
+
+        nobs_group = self._multicomp.groupstats.groupnobs
+        self.df_total_hsd = np.sum(nobs_group - 1)
+
+
     def __str__(self):
         return str(self._results_table)
 
     def summary(self):
         """Summary table that can be printed"""
         return self._results_table
 
+    def summary_frame(self):
+        """Summary DataFrame
+
+        The group columns are labeled as "group_t" and "group_c" with mean
+        difference defined as treatment minus control.
+        This should be less confusing than numeric labels group1 and group2.
+
+        Returns
+        -------
+        pandas.DataFrame
+
+        Notes
+        -----
+        The number of columns will likely increase in a future version of
+        statsmodels. Do not use numeric indices for the DataFrame in order
+       
```

### `statsmodels/stats/multicomp.py`
```diff
@@ -10,9 +10,9 @@
 __all__ = ['tukeyhsd', 'MultiComparison']
 
 
-def pairwise_tukeyhsd(endog, groups, alpha=0.05):
+def pairwise_tukeyhsd(endog, groups, alpha=0.05, use_var='equal'):
     """
-    Calculate all pairwise comparisons with TukeyHSD confidence intervals
+    Calculate all pairwise comparisons with TukeyHSD or Games-Howell.
 
     Parameters
     ----------
@@ -22,6 +22,13 @@ def pairwise_tukeyhsd(endog, groups, alpha=0.05):
         array with groups, can be string or integers
     alpha : float
         significance level for the test
+    use_var : {"unequal", "equal"}
+        If ``use_var`` is "equal", then the Tukey-hsd pvalues are returned.
+        Tukey-hsd assumes that (within) variances are the same across groups.
+        If ``use_var`` is "unequal", then the Games-Howell pvalues are
+        returned. This uses Welch's t-test for unequal variances with
+        Satterthwaite's corrected degrees of freedom for each pairwise
+        comparison.
 
     Returns
     -------
@@ -31,7 +38,17 @@ def pairwise_tukeyhsd(endog, groups, alpha=0.05):
 
     Notes
     -----
-    This is just a wrapper around tukeyhsd method of MultiComparison
+    This is just a wrapper around tukeyhsd method of MultiComparison.
+    Tukey-hsd is not robust to heteroscedasticity, i.e. variance differ across
+    groups, especially if group sizes also vary. In those cases, the actual
+    size (rejection rate under the Null hypothesis) might be far from the
+    nominal size of the test.
+    The Games-Howell method uses pairwise t-tests that are robust to differences
+    in variances and approximately maintains size unless samples are very
+    small.
+
+    .. versionadded:: 0.15
+   `   The `use_var` keyword and option for Games-Howell test.
 
     See Also
     --------
@@ -40,4 +57,5 @@ def pairwise_tukeyhsd(endog, groups, alpha=0.05):
     statsmodels.sandbox.stats.multicomp.TukeyHSDResults
     """
 
-    return MultiComparison(endog, groups).tukeyhsd(alpha=alph
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `statsmodels/sandbox/stats/multicomp.py`
- `statsmodels/stats/multicomp.py`
