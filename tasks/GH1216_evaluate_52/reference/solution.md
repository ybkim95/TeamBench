# Reference solution — GH1216_evaluate_52

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1216_evaluate_52`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1216_evaluate_52/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `measurements/word_length/word_length.py` (modified, +6/-1)
- `src/evaluate/utils/file_utils.py` (modified, +1/-1)
- `tests/test_metric_common.py` (modified, +1/-1)

## Diff Summary (What the Fix Changes)

### `measurements/word_length/word_length.py`
```diff
@@ -17,6 +17,7 @@
 import datasets
 from statistics import mean
 
+
 _DESCRIPTION = """
 Returns the average length (in terms of the number of words) of the input data.
 """
@@ -36,7 +37,7 @@
     >>> wordlength = evaluate.load("word_length", type="measurement")
     >>> results = wordlength.compute(data=data)
     >>> print(results)
-    {"average_word_length": 2}
+    {'average_word_length': 2}
 """
 
 # TODO: Add BibTeX citation
@@ -66,6 +67,10 @@ def _info(self):
             })
         )
 
+    def _download_and_prepare(self, dl_manager):
+        import nltk
+        nltk.download("punkt")
+
     def _compute(self, data, tokenizer=word_tokenize):
         """Returns the average word length of the input data"""
         lengths = [len(tokenizer(d)) for d in data]
```

### `src/evaluate/utils/file_utils.py`
```diff
@@ -104,7 +104,7 @@ def hf_github_url(path: str, name: str, type: str, revision: Optional[str] = Non
         return config.REPO_METRICS_URL.format(revision=revision, path=path, name=name)
     elif type == "comparison":
         return config.REPO_COMPARISONS_URL.format(revision=revision, path=path, name=name)
-    elif type == "measurements":
+    elif type == "measurement":
         return config.REPO_MEASUREMENTS_URL.format(revision=revision, path=path, name=name)
     else:
         raise TypeError(
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `measurements/word_length/word_length.py`
- `src/evaluate/utils/file_utils.py`
