# Reference solution — GH1112_scipy_24610

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1112_scipy_24610`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1112_scipy_24610/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `scipy/stats/_continuous_distns.py` (modified, +8/-5)
- `scipy/stats/_discrete_distns.py` (modified, +6/-7)
- `scipy/stats/_distribution_infrastructure.py` (modified, +0/-1)
- `scipy/stats/tests/test_continuous.py` (modified, +7/-4)

## Diff Summary (What the Fix Changes)

### `scipy/stats/_continuous_distns.py`
```diff
@@ -3377,6 +3377,7 @@ def _shape_info(self):
         return [_ShapeInfo("c", False, (-np.inf, np.inf), (False, False))]
 
     def _get_support(self, c):
+        c = np.asarray(c)
         _b = np.where(c > 0, 1.0 / np.maximum(c, _XMIN), np.inf)
         _a = np.where(c < 0, 1.0 / np.minimum(c, -_XMIN), -np.inf)
         return _a, _b
@@ -3493,6 +3494,7 @@ def _fitstart(self, data):
 
     def _munp(self, n, c):
         k = np.arange(0, n+1)
+        k = np.reshape(k, (-1,) + (1,)*c.ndim)
         vals = 1.0/c**n * np.sum(
             sc.comb(n, k) * (-1)**k * sc.gamma(c*k + 1),
             axis=0)
@@ -8071,8 +8073,6 @@ def _stats(self, df):
         return mu, mu2, g1, g2
 
     def _entropy(self, df):
-        if df == np.inf:
-            return norm._entropy()
 
         def regular(df):
             half = df/2
@@ -10867,9 +10867,12 @@ def _stats(self, lam):
         return 0, _tlvar(lam), 0, _tlkurt(lam)
 
     def _entropy(self, lam):
-        def integ(p):
-            return np.log(pow(p, lam-1)+pow(1-p, lam-1))
-        return integrate.quad(integ, 0, 1)[0]
+        @np.vectorize
+        def entropy_1d(lam):
+            def integ(p):
+                return np.log(pow(p, lam - 1) + pow(1 - p, lam - 1))
+            return integrate.quad(integ, 0, 1)[0]
+        return entropy_1d(lam)
 
 
 tukeylambda = tukeylambda_gen(name='tukeylambda')
```

### `scipy/stats/_discrete_distns.py`
```diff
@@ -66,7 +66,9 @@ def _shape_info(self):
                 _ShapeInfo("p", False, (0, 1), (True, True))]
 
     def _rvs(self, n, p, size=None, random_state=None):
-        return random_state.binomial(n, p, size)
+        if not np.all(n == np.floor(n)):
+            raise ValueError("`n` must be integral.")
+        return random_state.binomial(np.asarray(n, dtype=int), p, size)
 
     def _argcheck(self, n, p):
         return (n >= 0) & _isintegral(n) & (p >= 0) & (p <= 1)
@@ -115,11 +117,6 @@ def _stats(self, n, p, moments='mv'):
             g2 = t1 - t2
         return mu, var, g1, g2
 
-    def _entropy(self, n, p):
-        k = np.r_[0:n + 1]
-        vals = self._pmf(k, n, p)
-        return np.sum(entr(vals), axis=0)
-
 
 binom = binom_gen(name='binom')
 
@@ -235,7 +232,9 @@ def _shape_info(self):
 
     def _rvs(self, n, a, b, size=None, random_state=None):
         p = random_state.beta(a, b, size)
-        return random_state.binomial(n, p, size)
+        if not np.all(n == np.floor(n)):
+            raise ValueError("`n` must be integral.")
+        return random_state.binomial(np.asarray(n, dtype=int), p, size)
 
     def _get_support(self, n, a, b):
         return 0, n
```

### `scipy/stats/_distribution_infrastructure.py`
```diff
@@ -4000,7 +4000,6 @@ def logintegrand(x, **params):
 }
 
 
-# beta, genextreme, gengamma, t, tukeylambda need work for 1D arrays
 @xp_capabilities(np_only=True)
 def make_distribution(dist):
     """Generate a `UnivariateDistribution` class from a compatible object.
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `scipy/stats/_continuous_distns.py`
- `scipy/stats/_discrete_distns.py`
- `scipy/stats/_distribution_infrastructure.py`
