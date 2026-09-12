# Reference solution — GH1072_spaCy_13321

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1072_spaCy_13321`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1072_spaCy_13321/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `spacy/errors.py` (modified, +1/-0)
- `spacy/language.py` (modified, +5/-0)
- `spacy/tests/test_language.py` (modified, +8/-3)

## Diff Summary (What the Fix Changes)

### `spacy/errors.py`
```diff
@@ -220,6 +220,7 @@ class Warnings(metaclass=ErrorsWithCodes):
             "key attribute for vectors, configure it through Vectors(attr=) or "
             "'spacy init vectors --attr'")
     W126 = ("These keys are unsupported: {unsupported}")
+    W127 = ("Not all `Language.pipe` worker processes completed successfully")
 
 
 class Errors(metaclass=ErrorsWithCodes):
```

### `spacy/language.py`
```diff
@@ -1730,6 +1730,9 @@ def prepare_input(
             for proc in procs:
                 proc.join()
 
+            if not all(proc.exitcode == 0 for proc in procs):
+                warnings.warn(Warnings.W127)
+
     def _link_components(self) -> None:
         """Register 'listeners' within pipeline components, to allow them to
         effectively share weights.
@@ -2350,6 +2353,7 @@ def _apply_pipes(
             if isinstance(texts_with_ctx, _WorkDoneSentinel):
                 sender.close()
                 receiver.close()
+                return
 
             docs = (
                 ensure_doc(doc_like, context) for doc_like, context in texts_with_ctx
@@ -2375,6 +2379,7 @@ def _apply_pipes(
             # stop processing.
             sender.close()
             receiver.close()
+            return
 
 
 class _Sender:
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `spacy/errors.py`
- `spacy/language.py`
