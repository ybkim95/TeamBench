# Reference solution — GH1008_spaCy_12749

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1008_spaCy_12749`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1008_spaCy_12749/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `spacy/cli/debug_data.py` (modified, +3/-3)
- `spacy/tests/test_cli.py` (modified, +3/-2)

## Diff Summary (What the Fix Changes)

### `spacy/cli/debug_data.py`
```diff
@@ -230,7 +230,7 @@ def debug_data(
     else:
         msg.info("No word vectors present in the package")
 
-    if "spancat" in factory_names:
+    if "spancat" in factory_names or "spancat_singlelabel" in factory_names:
         model_labels_spancat = _get_labels_from_spancat(nlp)
         has_low_data_warning = False
         has_no_neg_warning = False
@@ -848,7 +848,7 @@ def _compile_gold(
                     data["boundary_cross_ents"] += 1
                 elif label == "-":
                     data["ner"]["-"] += 1
-        if "spancat" in factory_names:
+        if "spancat" in factory_names or "spancat_singlelabel" in factory_names:
             for spans_key in list(eg.reference.spans.keys()):
                 # Obtain the span frequency
                 if spans_key not in data["spancat"]:
@@ -1046,7 +1046,7 @@ def _get_labels_from_spancat(nlp: Language) -> Dict[str, Set[str]]:
     pipe_names = [
         pipe_name
         for pipe_name in nlp.pipe_names
-        if nlp.get_pipe_meta(pipe_name).factory == "spancat"
+        if nlp.get_pipe_meta(pipe_name).factory in ("spancat", "spancat_singlelabel")
     ]
     labels: Dict[str, Set[str]] = {}
     for pipe_name in pipe_names:
```

## Moved from `brief.md`

## Files That May Need Changes

- `spacy/cli/debug_data.py`
