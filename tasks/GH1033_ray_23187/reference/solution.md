# Reference solution — GH1033_ray_23187

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1033_ray_23187`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1033_ray_23187/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `python/ray/tests/test_actor_pool.py` (modified, +23/-0)
- `python/ray/util/actor_pool.py` (modified, +16/-0)

## Diff Summary (What the Fix Changes)

### `python/ray/util/actor_pool.py`
```diff
@@ -59,6 +59,14 @@ def map(self, fn, values):
             ...                     [1, 2, 3, 4])))
             [2, 4, 6, 8]
         """
+        # Ignore/Cancel all the previous submissions
+        # by calling `has_next` and `gen_next` repeteadly.
+        while self.has_next():
+            try:
+                self.get_next(timeout=0)
+            except TimeoutError:
+                pass
+
         for v in values:
             self.submit(fn, v)
         while self.has_next():
@@ -87,6 +95,14 @@ def map_unordered(self, fn, values):
             ...                               [1, 2, 3, 4])))
             [6, 2, 4, 8]
         """
+        # Ignore/Cancel all the previous submissions
+        # by calling `has_next` and `gen_next_unordered` repeteadly.
+        while self.has_next():
+            try:
+                self.get_next_unordered(timeout=0)
+            except TimeoutError:
+                pass
+
         for v in values:
             self.submit(fn, v)
         while self.has_next():
```

## Moved from `brief.md`

## Files That May Need Changes

- `python/ray/util/actor_pool.py`
