# Reference solution — GH1093_spaCy_8012

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1093_spaCy_8012`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1093_spaCy_8012/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `spacy/pipeline/tok2vec.py` (modified, +1/-0)
- `spacy/tests/pipeline/test_tok2vec.py` (modified, +91/-2)

## Diff Summary (What the Fix Changes)

### `spacy/pipeline/tok2vec.py`
```diff
@@ -173,6 +173,7 @@ def accumulate_gradient(one_d_tokvecs):
             for i in range(len(one_d_tokvecs)):
                 d_tokvecs[i] += one_d_tokvecs[i]
                 losses[self.name] += float((one_d_tokvecs[i] ** 2).sum())
+            return [self.model.ops.alloc2f(*t2v.shape) for t2v in tokvecs]
 
         def backprop(one_d_tokvecs):
             """Callback to actually do the backprop. Passed to last listener."""
```

## Moved from `brief.md`

## Files That May Need Changes

- `spacy/pipeline/tok2vec.py`
