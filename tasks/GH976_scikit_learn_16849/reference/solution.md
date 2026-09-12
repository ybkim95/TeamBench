# Reference solution — GH976_scikit_learn_16849

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH976_scikit_learn_16849`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH976_scikit_learn_16849/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/whats_new/v0.23.rst` (modified, +6/-0)
- `sklearn/externals/_scipy_linalg.py` (removed, +0/-118)
- `sklearn/linear_model/_bayes.py` (modified, +41/-18)
- `sklearn/linear_model/tests/test_bayes.py` (modified, +36/-12)
- `sklearn/utils/fixes.py` (modified, +0/-8)

## Diff Summary (What the Fix Changes)

### `sklearn/externals/_scipy_linalg.py`
```diff
@@ -1,118 +0,0 @@
-# This should remained pinned to version 1.2 and not updated like other
-# externals.
-"""Copyright (c) 2001-2002 Enthought, Inc.  2003-2019, SciPy Developers.
-All rights reserved.
-
-Redistribution and use in source and binary forms, with or without
-modification, are permitted provided that the following conditions
-are met:
-
-1. Redistributions of source code must retain the above copyright
-   notice, this list of conditions and the following disclaimer.
-
-2. Redistributions in binary form must reproduce the above
-   copyright notice, this list of conditions and the following
-   disclaimer in the documentation and/or other materials provided
-   with the distribution.
-
-3. Neither the name of the copyright holder nor the names of its
-   contributors may be used to endorse or promote products derived
-   from this software without specific prior written permission.
-
-THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
-"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
-LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
-A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
-OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
-SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
-LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
-DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
-THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
-(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
-OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
-"""
-
-import numpy as np
-import scipy.linalg.decomp as decomp
-
-
-def pinvh(a, cond=None, rcond=None, lower=True, return_rank=False,
-          check_finite=True):
-    """
-    Compute the (Moore-Penrose) pseudo-inverse of a Hermitian matrix.
-
-    Copied in from scipy==1.2.2, in order to preserve the default choice o
```

### `sklearn/linear_model/_bayes.py`
```diff
@@ -12,7 +12,7 @@
 from ._base import LinearModel, _rescale_data
 from ..base import RegressorMixin
 from ..utils.extmath import fast_logdet
-from ..utils.fixes import pinvh
+from scipy.linalg import pinvh
 from ..utils.validation import _check_sample_weight
 from ..utils.validation import _deprecate_positional_args
 
@@ -554,27 +554,16 @@ def fit(self, X, y):
         self.scores_ = list()
         coef_old_ = None
 
-        # Compute sigma and mu (using Woodbury matrix identity)
-        def update_sigma(X, alpha_, lambda_, keep_lambda, n_samples):
-            sigma_ = pinvh(np.eye(n_samples) / alpha_ +
-                           np.dot(X[:, keep_lambda] *
-                           np.reshape(1. / lambda_[keep_lambda], [1, -1]),
-                           X[:, keep_lambda].T))
-            sigma_ = np.dot(sigma_, X[:, keep_lambda] *
-                            np.reshape(1. / lambda_[keep_lambda], [1, -1]))
-            sigma_ = - np.dot(np.reshape(1. / lambda_[keep_lambda], [-1, 1]) *
-                              X[:, keep_lambda].T, sigma_)
-            sigma_.flat[::(sigma_.shape[1] + 1)] += 1. / lambda_[keep_lambda]
-            return sigma_
-
         def update_coeff(X, y, coef_, alpha_, keep_lambda, sigma_):
             coef_[keep_lambda] = alpha_ * np.dot(
                 sigma_, np.dot(X[:, keep_lambda].T, y))
             return coef_
 
+        update_sigma = (self._update_sigma if n_samples >= n_features
+                        else self._update_sigma_woodbury)
         # Iterative procedure of ARDRegression
         for iter_ in range(self.n_iter):
-            sigma_ = update_sigma(X, alpha_, lambda_, keep_lambda, n_samples)
+            sigma_ = update_sigma(X, alpha_, lambda_, keep_lambda)
             coef_ = update_coeff(X, y, coef_, alpha_, keep_lambda, sigma_)
 
             # Update alpha and lambda
@@ -606,9 +595,15 @@ def update_coeff(X, y, coef_, alpha_, keep_lambda, sigma_):
                 break
             coef_old_ = np.c
```

### `sklearn/utils/fixes.py`
```diff
@@ -42,14 +42,6 @@ def _parse_version(version_string):
     # mypy error: Name 'lobpcg' already defined (possibly by an import)
     from ..externals._lobpcg import lobpcg  # type: ignore  # noqa
 
-if sp_version >= (1, 3):
-    # Preserves earlier default choice of pinvh cutoff `cond` value.
-    # Can be removed once issue #14055 is fully addressed.
-    from ..externals._scipy_linalg import pinvh
-else:
-    # mypy error: Name 'pinvh' already defined (possibly by an import)
-    from scipy.linalg import pinvh  # type: ignore  # noqa
-
 
 def _object_dtype_isnan(X):
     return X != X
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `sklearn/externals/_scipy_linalg.py`
- `sklearn/linear_model/_bayes.py`
- `sklearn/utils/fixes.py`
