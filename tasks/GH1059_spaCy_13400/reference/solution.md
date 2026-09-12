# Reference solution — GH1059_spaCy_13400

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1059_spaCy_13400`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1059_spaCy_13400/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `spacy/pipeline/entity_linker.py` (modified, +39/-24)
- `spacy/tests/pipeline/test_entity_linker.py` (modified, +105/-2)
- `website/docs/api/entitylinker.mdx` (modified, +1/-1)

## Diff Summary (What the Fix Changes)

### `spacy/pipeline/entity_linker.py`
```diff
@@ -11,7 +11,6 @@
 from ..errors import Errors
 from ..kb import Candidate, KnowledgeBase
 from ..language import Language
-from ..ml import empty_kb
 from ..scorer import Scorer
 from ..tokens import Doc, Span
 from ..training import Example, validate_examples, validate_get_examples
@@ -105,7 +104,7 @@ def make_entity_linker(
         ): Function that produces a list of candidates, given a certain knowledge base and several textual mentions.
     generate_empty_kb (Callable[[Vocab, int], KnowledgeBase]): Callable returning empty KnowledgeBase.
     scorer (Optional[Callable]): The scoring method.
-    use_gold_ents (bool): Whether to copy entities from gold docs or not. If false, another
+    use_gold_ents (bool): Whether to copy entities from gold docs during training or not. If false, another
         component must provide entity annotations.
     candidates_batch_size (int): Size of batches for entity candidate generation.
     threshold (Optional[float]): Confidence threshold for entity predictions. If confidence is below the threshold,
@@ -235,14 +234,44 @@ def __init__(
         self.cfg: Dict[str, Any] = {"overwrite": overwrite}
         self.distance = CosineDistance(normalize=False)
         self.kb = generate_empty_kb(self.vocab, entity_vector_length)
-        self.scorer = scorer
         self.use_gold_ents = use_gold_ents
         self.candidates_batch_size = candidates_batch_size
         self.threshold = threshold
 
         if candidates_batch_size < 1:
             raise ValueError(Errors.E1044)
 
+        def _score_with_ents_set(examples: Iterable[Example], **kwargs):
+            # Because of how spaCy works, we can't just score immediately, because Language.evaluate
+            # calls pipe() on the predicted docs, which won't have entities if there is no NER in the pipeline.
+            if not scorer:
+                return scorer
+            if not self.use_gold_ents:
+                return scorer(examples, **kwargs)
+            else:
+
```

## Moved from `brief.md`

## Files That May Need Changes

- `spacy/pipeline/entity_linker.py`
