# Reference solution — GH1073_spaCy_13249

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1073_spaCy_13249`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1073_spaCy_13249/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `spacy/ml/models/textcat.py` (modified, +14/-1)
- `spacy/tests/pipeline/test_textcat.py` (modified, +37/-0)
- `spacy/tests/tok2vec.py` (added, +36/-0)

## Diff Summary (What the Fix Changes)

### `spacy/ml/models/textcat.py`
```diff
@@ -185,6 +185,11 @@ def build_text_classifier_v2(
 
 
 def init_ensemble_textcat(model, X, Y) -> Model:
+    # When tok2vec is lazily initialized, we need to initialize it before
+    # the rest of the chain to ensure that we can get its width.
+    tok2vec = model.get_ref("tok2vec")
+    tok2vec.initialize(X)
+
     tok2vec_width = get_tok2vec_width(model)
     model.get_ref("attention_layer").set_dim("nO", tok2vec_width)
     model.get_ref("maxout_layer").set_dim("nO", tok2vec_width)
@@ -264,17 +269,25 @@ def _build_parametric_attention_with_residual_nonlinear(
 
         parametric_attention.set_ref("tok2vec", tok2vec)
         parametric_attention.set_ref("attention_layer", attention_layer)
+        parametric_attention.set_ref("key_transform", key_transform)
         parametric_attention.set_ref("nonlinear_layer", nonlinear_layer)
         parametric_attention.set_ref("norm_layer", norm_layer)
 
         return parametric_attention
 
 
 def _init_parametric_attention_with_residual_nonlinear(model, X, Y) -> Model:
+    # When tok2vec is lazily initialized, we need to initialize it before
+    # the rest of the chain to ensure that we can get its width.
+    tok2vec = model.get_ref("tok2vec")
+    tok2vec.initialize(X)
+
     tok2vec_width = get_tok2vec_width(model)
     model.get_ref("attention_layer").set_dim("nO", tok2vec_width)
-    model.get_ref("nonlinear_layer").set_dim("nO", tok2vec_width)
+    model.get_ref("key_transform").set_dim("nI", tok2vec_width)
+    model.get_ref("key_transform").set_dim("nO", tok2vec_width)
     model.get_ref("nonlinear_layer").set_dim("nI", tok2vec_width)
+    model.get_ref("nonlinear_layer").set_dim("nO", tok2vec_width)
     model.get_ref("norm_layer").set_dim("nI", tok2vec_width)
     model.get_ref("norm_layer").set_dim("nO", tok2vec_width)
     init_chain(model, X, Y)
```

## Moved from `brief.md`

## Files That May Need Changes

- `spacy/ml/models/textcat.py`
