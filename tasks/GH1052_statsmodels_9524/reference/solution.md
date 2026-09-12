# Reference solution — GH1052_statsmodels_9524

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1052_statsmodels_9524`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1052_statsmodels_9524/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `statsmodels/sandbox/stats/runs.py` (modified, +7/-2)
- `statsmodels/sandbox/stats/tests/test_runs.py` (modified, +7/-0)

## Diff Summary (What the Fix Changes)

### `statsmodels/sandbox/stats/runs.py`
```diff
@@ -77,18 +77,23 @@ def runs_test(self, correction=True):
             does not use any correction.
 
         pvalue based on normal distribution, with integer correction
+        if a single run is detected, pvalue is based on the Binomial distribition
 
         '''
         self.npo = npo = (self.runs_pos).sum()
         self.nne = nne = (self.runs_neg).sum()
 
-        #n_r = self.n_runs
+        n_r = self.n_runs
         n = npo + nne
+        if n_r == 1:
+            pval = 1 / (2.0 ** (min(n,1024) - 1))
+            z = -stats.norm.isf(pval)
+            return z, pval*2
         npn = npo * nne
         rmean = 2. * npn / n + 1
         rvar = 2. * npn * (2.*npn - n) / n**2. / (n-1.)
         rstd = np.sqrt(rvar)
-        rdemean = self.n_runs - rmean
+        rdemean = n_r - rmean
         if n >= 50 or not correction:
             z = rdemean
         else:
```

## Moved from `brief.md`

## Files That May Need Changes

- `statsmodels/sandbox/stats/runs.py`
