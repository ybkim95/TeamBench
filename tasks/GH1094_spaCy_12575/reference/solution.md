# Reference solution — GH1094_spaCy_12575

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1094_spaCy_12575`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1094_spaCy_12575/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `spacy/cli/evaluate.py` (modified, +9/-0)
- `spacy/tests/test_cli.py` (modified, +66/-0)

## Diff Summary (What the Fix Changes)

### `spacy/cli/evaluate.py`
```diff
@@ -122,13 +122,16 @@ def evaluate(
         docs = list(nlp.pipe(ex.reference.text for ex in dev_dataset[:displacy_limit]))
         render_deps = "parser" in factory_names
         render_ents = "ner" in factory_names
+        render_spans = "spancat" in factory_names
+
         render_parses(
             docs,
             displacy_path,
             model_name=model,
             limit=displacy_limit,
             deps=render_deps,
             ents=render_ents,
+            spans=render_spans,
         )
         msg.good(f"Generated {displacy_limit} parses as HTML", displacy_path)
 
@@ -182,6 +185,7 @@ def render_parses(
     limit: int = 250,
     deps: bool = True,
     ents: bool = True,
+    spans: bool = True,
 ):
     docs[0].user_data["title"] = model_name
     if ents:
@@ -195,6 +199,11 @@ def render_parses(
         with (output_path / "parses.html").open("w", encoding="utf8") as file_:
             file_.write(html)
 
+    if spans:
+        html = displacy.render(docs[:limit], style="span", page=True)
+        with (output_path / "spans.html").open("w", encoding="utf8") as file_:
+            file_.write(html)
+
 
 def print_prf_per_type(
     msg: Printer, scores: Dict[str, Dict[str, float]], name: str, type: str
```

## Moved from `brief.md`

## Files That May Need Changes

- `spacy/cli/evaluate.py`
