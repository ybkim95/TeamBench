# Reference solution — GH1028_statsmodels_8633

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1028_statsmodels_8633`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1028_statsmodels_8633/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `statsmodels/distributions/copula/_special.py` (added, +110/-0)
- `statsmodels/distributions/copula/archimedean.py` (modified, +84/-53)
- `statsmodels/distributions/copula/copulas.py` (modified, +0/-3)
- `statsmodels/distributions/copula/extreme_value.py` (modified, +2/-0)
- `statsmodels/distributions/copula/other_copulas.py` (modified, +3/-2)
- `statsmodels/distributions/copula/tests/test_copula.py` (modified, +84/-17)
- `statsmodels/distributions/copula/transforms.py` (modified, +94/-1)

## Diff Summary (What the Fix Changes)

### `statsmodels/distributions/copula/_special.py`
```diff
@@ -0,0 +1,110 @@
+"""
+
+Special functions for copulas not available in scipy
+
+Created on Jan. 27, 2023
+"""
+
+import numpy as np
+from scipy.special import factorial
+
+
+class Sterling1():
+    """Stirling numbers of the first kind
+    """
+    # based on
+    # https://rosettacode.org/wiki/Stirling_numbers_of_the_first_kind#Python
+
+    def __init__(self):
+        self._cache = {}
+
+    def __call__(self, n, k):
+        key = str(n) + "," + str(k)
+
+        if key in self._cache.keys():
+            return self._cache[key]
+        if n == k == 0:
+            return 1
+        if n > 0 and k == 0:
+            return 0
+        if k > n:
+            return 0
+        result = sterling1(n - 1, k - 1) + (n - 1) * sterling1(n - 1, k)
+        self._cache[key] = result
+        return result
+
+    def clear_cache(self):
+        """clear cache of Sterling numbers
+        """
+        self._cache = {}
+
+
+sterling1 = Sterling1()
+
+
+class Sterling2():
+    """Stirling numbers of the second kind
+    """
+    # based on
+    # https://rosettacode.org/wiki/Stirling_numbers_of_the_second_kind#Python
+
+    def __init__(self):
+        self._cache = {}
+
+    def __call__(self, n, k):
+        key = str(n) + "," + str(k)
+
+        if key in self._cache.keys():
+            return self._cache[key]
+        if n == k == 0:
+            return 1
+        if (n > 0 and k == 0) or (n == 0 and k > 0):
+            return 0
+        if n == k:
+            return 1
+        if k > n:
+            return 0
+        result = k * sterling2(n - 1, k) + sterling2(n - 1, k - 1)
+        self._cache[key] = result
+        return result
+
+    def clear_cache(self):
+        """clear cache of Sterling numbers
+        """
+        self._cache = {}
+
+
+sterling2 = Sterling2()
+
+
+def li3(z):
+    """Polylogarithm for negative integer order -3
+
+    Li(-3, z)
+    """
+    return z * (1 + 4 * z + z**2) / (1 - z)**4
+
+
+def li4(z):
+    """Polylogarithm for negative in
```

### `statsmodels/distributions/copula/archimedean.py`
```diff
@@ -63,9 +63,20 @@ def _handle_args(self, args):
 
         return args
 
+    def _handle_u(self, u):
+        u = np.asarray(u)
+        if u.shape[-1] != self.k_dim:
+            import warnings
+            warnings.warn("u has different dimension than k_dim. "
+                          "This will raise exception in future versions",
+                          FutureWarning)
+
+        return u
+
     def cdf(self, u, args=()):
         """Evaluate cdf of Archimedean copula."""
         args = self._handle_args(args)
+        u = self._handle_u(u)
         axis = -1
         phi = self.transform.evaluate
         phi_inv = self.transform.inverse
@@ -77,44 +88,59 @@ def cdf(self, u, args=()):
 
     def pdf(self, u, args=()):
         """Evaluate pdf of Archimedean copula."""
+        u = self._handle_u(u)
         args = self._handle_args(args)
         axis = -1
-        u = np.asarray(u)
-        if u.shape[-1] > 2:
-            msg = "pdf is currently only available for bivariate copula"
-            raise ValueError(msg)
-        # phi = self.transform.evaluate
-        # phi_inv = self.transform.inverse
+
         phi_d1 = self.transform.deriv
-        phi_d2 = self.transform.deriv2
+        if u.shape[-1] == 2:
+            psi_d = self.transform.deriv2_inverse
+        elif u.shape[-1] == 3:
+            psi_d = self.transform.deriv3_inverse
+        elif u.shape[-1] == 4:
+            psi_d = self.transform.deriv4_inverse
+        else:
+            # will raise NotImplementedError if not available
+            k = u.shape[-1]
 
-        cdfv = self.cdf(u, args=args)
+            def psi_d(*args):
+                return self.transform.derivk_inverse(k, *args)
 
-        pdfv = - np.product(phi_d1(u, *args), axis)
-        pdfv *= phi_d2(cdfv, *args)
-        pdfv /= phi_d1(cdfv, *args)**3
+        psi = self.transform.evaluate(u, *args).sum(axis)
 
-        return pdfv
+        pdfv = np.product(phi_d1(u, *args), axis)
+        pdfv *= (psi_d(psi, *arg
```

### `statsmodels/distributions/copula/copulas.py`
```diff
@@ -264,9 +264,6 @@ class Copula(ABC):
 
     def __init__(self, k_dim=2):
         self.k_dim = k_dim
-        if k_dim > 2:
-            import warnings
-            warnings.warn("copulas for more than 2 dimension is untested")
 
     def rvs(self, nobs=1, args=(), random_state=None):
         """Draw `n` in the half-open interval ``[0, 1)``.
```

### `statsmodels/distributions/copula/extreme_value.py`
```diff
@@ -56,6 +56,8 @@ def __init__(self, transform, args=(), k_dim=2):
         self.transform = transform
         self.k_args = transform.k_args
         self.args = args
+        if k_dim != 2:
+            raise ValueError("Only bivariate EV copulas are available.")
 
     def _handle_args(self, args):
         # TODO: how to we handle non-tuple args? two we allow single values?
```

### `statsmodels/distributions/copula/other_copulas.py`
```diff
@@ -52,10 +52,11 @@ def rvs(self, nobs=1, args=(), random_state=None):
         return x
 
     def pdf(self, u, args=()):
-        return np.ones(len(u))
+        u = np.asarray(u)
+        return np.ones(u.shape[:-1])
 
     def cdf(self, u, args=()):
-        return np.prod(u, axis=1)
+        return np.prod(u, axis=-1)
 
     def tau(self):
         return 0
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `statsmodels/distributions/copula/_special.py`
- `statsmodels/distributions/copula/archimedean.py`
- `statsmodels/distributions/copula/copulas.py`
- `statsmodels/distributions/copula/extreme_value.py`
- `statsmodels/distributions/copula/other_copulas.py`
