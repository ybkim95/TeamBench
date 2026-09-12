# Reference solution — GH884_sktime_9243

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH884_sktime_9243`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH884_sktime_9243/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `sktime/transformations/series/summarize.py` (modified, +4/-2)
- `sktime/transformations/series/tests/test_window_summarizer.py` (modified, +32/-0)

## Diff Summary (What the Fix Changes)

### `sktime/transformations/series/summarize.py`
```diff
@@ -481,9 +481,11 @@ class description for in-depth explanation.
         raise ValueError("The provided summarizer is not callable.")
     feat = pd.DataFrame(feat)
 
-    # Handle backfill
     if bfill is True:
-        feat = feat.bfill()
+        if hasattr(Z, "grouper"):
+            feat = feat.groupby(Z.grouper).bfill()
+        else:
+            feat = feat.bfill()
 
     if callable(summarizer):
         name = summarizer.__name__
```

## Moved from `brief.md`

## Files That May Need Changes

- `sktime/transformations/series/summarize.py`
