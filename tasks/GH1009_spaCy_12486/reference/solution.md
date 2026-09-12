# Reference solution — GH1009_spaCy_12486

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1009_spaCy_12486`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1009_spaCy_12486/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `spacy/pipeline/spancat.py` (modified, +31/-27)
- `spacy/tests/pipeline/test_spancat.py` (modified, +19/-1)

## Diff Summary (What the Fix Changes)

### `spacy/pipeline/spancat.py`
```diff
@@ -1,5 +1,6 @@
 from typing import List, Dict, Callable, Tuple, Optional, Iterable, Any, cast, Union
 from dataclasses import dataclass
+from functools import partial
 from thinc.api import Config, Model, get_current_ops, set_dropout_rate, Ops
 from thinc.api import Optimizer
 from thinc.types import Ragged, Ints2d, Floats2d
@@ -82,39 +83,42 @@ def __call__(self, docs: Iterable[Doc], *, ops: Optional[Ops] = None) -> Ragged:
         ...
 
 
+def ngram_suggester(
+    docs: Iterable[Doc], sizes: List[int], *, ops: Optional[Ops] = None
+) -> Ragged:
+    if ops is None:
+        ops = get_current_ops()
+    spans = []
+    lengths = []
+    for doc in docs:
+        starts = ops.xp.arange(len(doc), dtype="i")
+        starts = starts.reshape((-1, 1))
+        length = 0
+        for size in sizes:
+            if size <= len(doc):
+                starts_size = starts[: len(doc) - (size - 1)]
+                spans.append(ops.xp.hstack((starts_size, starts_size + size)))
+                length += spans[-1].shape[0]
+            if spans:
+                assert spans[-1].ndim == 2, spans[-1].shape
+        lengths.append(length)
+    lengths_array = ops.asarray1i(lengths)
+    if len(spans) > 0:
+        output = Ragged(ops.xp.vstack(spans), lengths_array)
+    else:
+        output = Ragged(ops.xp.zeros((0, 0), dtype="i"), lengths_array)
+
+    assert output.dataXd.ndim == 2
+    return output
+
+
 @registry.misc("spacy.ngram_suggester.v1")
 def build_ngram_suggester(sizes: List[int]) -> Suggester:
     """Suggest all spans of the given lengths. Spans are returned as a ragged
     array of integers. The array has two columns, indicating the start and end
     position."""
 
-    def ngram_suggester(docs: Iterable[Doc], *, ops: Optional[Ops] = None) -> Ragged:
-        if ops is None:
-            ops = get_current_ops()
-        spans = []
-        lengths = []
-        for doc in docs:
-            starts = ops.xp.arange(len(doc), dtype="i")
-            starts = 
```

## Moved from `brief.md`

## Files That May Need Changes

- `spacy/pipeline/spancat.py`
