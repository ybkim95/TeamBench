# Reference solution — GH962_ray_22048

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH962_ray_22048`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH962_ray_22048/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `python/ray/tests/test_multiprocessing.py` (modified, +22/-0)
- `python/ray/util/multiprocessing/pool.py` (modified, +1/-1)

## Diff Summary (What the Fix Changes)

### `python/ray/util/multiprocessing/pool.py`
```diff
@@ -435,7 +435,7 @@ def next(self, timeout=None):
         return self._ready_objects.popleft()
 
 
-@ray.remote(num_cpus=1)
+@ray.remote(num_cpus=0)
 class PoolActor:
     """Actor used to process tasks submitted to a Pool."""
 
```

## Moved from `brief.md`

## Files That May Need Changes

- `python/ray/util/multiprocessing/pool.py`
