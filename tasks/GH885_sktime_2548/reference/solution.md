# Reference solution — GH885_sktime_2548

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH885_sktime_2548`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH885_sktime_2548/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `sktime/clustering/k_medoids.py` (modified, +7/-2)
- `sktime/clustering/tests/test_k_medoids.py` (modified, +4/-5)

## Diff Summary (What the Fix Changes)

### `sktime/clustering/k_medoids.py`
```diff
@@ -129,9 +129,14 @@ def _compute_new_cluster_centers(
             curr_indexes = np.where(assignment_indexes == i)[0]
             distance_matrix = np.zeros((len(curr_indexes), len(curr_indexes)))
             for j in range(len(curr_indexes)):
+                curr_j = curr_indexes[j]
                 for k in range(len(curr_indexes)):
-                    distance_matrix[j, k] = self._precomputed_pairwise[j, k]
-            result = medoids(X[curr_indexes], self._precomputed_pairwise)
+                    distance_matrix[j, k] = self._precomputed_pairwise[
+                        curr_j, curr_indexes[k]
+                    ]
+            result = medoids(
+                X[curr_indexes], precomputed_pairwise_distance=distance_matrix
+            )
             if result.shape[0] > 0:
                 new_centers[i, :] = result
         return new_centers
```

## Moved from `brief.md`

## Files That May Need Changes

- `sktime/clustering/k_medoids.py`
