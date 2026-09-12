# Reference solution — GH878_FLAML_848

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH878_FLAML_848`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH878_FLAML_848/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `.github/workflows/python-package.yml` (modified, +1/-1)
- `flaml/automl/automl.py` (modified, +43/-34)
- `flaml/tune/searcher/blendsearch.py` (modified, +5/-4)
- `test/automl/__init__.py` (added, +0/-0)
- `test/automl/test_multiclass.py` (modified, +89/-59)
- `test/automl/test_python_log.py` (modified, +1/-1)
- `test/automl/test_training_log.py` (modified, +3/-1)

## Diff Summary (What the Fix Changes)

### `flaml/automl/automl.py`
```diff
@@ -141,31 +141,34 @@ def __init__(
         if custom_hp is not None:
             search_space.update(custom_hp)
 
-        if (
-            isinstance(starting_point, dict)
-            and max_iter
-            > 1  # If the number of starting point is larger than max iter, avoid the checking
-            and not self.valid_starting_point(starting_point, search_space)
-        ):
-            logger.warning(
-                "Starting point {} removed because it is outside of the search space".format(
-                    starting_point
-                )
-            )
-            starting_point = None
-        elif isinstance(starting_point, list) and max_iter > len(
-            starting_point
-        ):  # If the number of starting point is larger than max iter, avoid the checking
-            starting_point_len = len(starting_point)
-            starting_point = [
-                x for x in starting_point if self.valid_starting_point(x, search_space)
-            ]
-            if starting_point_len > len(starting_point):
+        if isinstance(starting_point, dict):
+            starting_point = AutoMLState.sanitize(starting_point)
+            if max_iter > 1 and not self.valid_starting_point(
+                starting_point, search_space
+            ):
+                # If the number of iterations is larger than 1, remove invalid point
                 logger.warning(
-                    "Starting points outside of the search space are removed. "
-                    f"Remaining starting points for {learner_class}: {starting_point}"
+                    "Starting point {} removed because it is outside of the search space".format(
+                        starting_point
+                    )
                 )
-            starting_point = starting_point or None
+                starting_point = None
+        elif isinstance(starting_point, list):
+            starting_point = [AutoMLState.sanitize(x) for x in starting_point]
+            if max_i
```

### `flaml/tune/searcher/blendsearch.py`
```diff
@@ -653,10 +653,11 @@ def _expand_admissible_region(self, lower, upper, space):
         for key in upper:
             ub = upper[key]
             if isinstance(ub, list):
-                choice = space[key]["_choice_"]
-                self._expand_admissible_region(
-                    lower[key][choice], upper[key][choice], space[key]
-                )
+                choice = space[key].get("_choice_")
+                if choice:
+                    self._expand_admissible_region(
+                        lower[key][choice], upper[key][choice], space[key]
+                    )
             elif isinstance(ub, dict):
                 self._expand_admissible_region(lower[key], ub, space[key])
             else:
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `flaml/automl/automl.py`
- `flaml/tune/searcher/blendsearch.py`
