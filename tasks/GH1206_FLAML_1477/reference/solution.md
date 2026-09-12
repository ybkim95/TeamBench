# Reference solution — GH1206_FLAML_1477

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1206_FLAML_1477`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1206_FLAML_1477/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `flaml/tune/searcher/blendsearch.py` (modified, +19/-2)
- `test/tune/test_searcher.py` (modified, +23/-0)

## Diff Summary (What the Fix Changes)

### `flaml/tune/searcher/blendsearch.py`
```diff
@@ -217,7 +217,24 @@ def __init__(
         if global_search_alg is not None:
             self._gs = global_search_alg
         elif getattr(self, "__name__", None) != "CFO":
-            if space and self._ls.hierarchical:
+            # Use define-by-run for OptunaSearch when needed:
+            # - Hierarchical/conditional spaces are best supported via define-by-run.
+            # - Ray Tune domain/grid specs can trigger an "unresolved search space" warning
+            #   unless we switch to define-by-run.
+            use_define_by_run = bool(getattr(self._ls, "hierarchical", False))
+            if (not use_define_by_run) and isinstance(space, dict) and space:
+                try:
+                    from .variant_generator import parse_spec_vars
+
+                    _, domain_vars, grid_vars = parse_spec_vars(space)
+                    use_define_by_run = bool(domain_vars or grid_vars)
+                except Exception:
+                    # Be conservative: if we can't determine whether the space is
+                    # unresolved, fall back to the original behavior.
+                    use_define_by_run = False
+
+            self._use_define_by_run = use_define_by_run
+            if use_define_by_run:
                 from functools import partial
 
                 gs_space = partial(define_by_run_func, space=space)
@@ -487,7 +504,7 @@ def on_trial_complete(self, trial_id: str, result: Optional[Dict] = None, error:
                             self._ls_bound_max,
                             self._subspace.get(trial_id, self._ls.space),
                         )
-                    if self._gs is not None and self._experimental and (not self._ls.hierarchical):
+                    if self._gs is not None and self._experimental and (not getattr(self, "_use_define_by_run", False)):
                         self._gs.add_evaluated_point(flatten_dict(config), objective)
                         # TODO: recover whe
```

## Moved from `brief.md`

## Files That May Need Changes

- `flaml/tune/searcher/blendsearch.py`
