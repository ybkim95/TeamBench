# Reference solution — GH1168_featuretools_2413

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1168_featuretools_2413`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1168_featuretools_2413/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/source/release_notes.rst` (modified, +1/-0)
- `featuretools/primitives/standard/transform/natural_language/number_of_words_in_quotes.py` (modified, +3/-3)
- `featuretools/tests/primitive_tests/natural_language_primitives_tests/test_number_of_words_in_quotes.py` (modified, +2/-1)

## Diff Summary (What the Fix Changes)

### `featuretools/primitives/standard/transform/natural_language/number_of_words_in_quotes.py`
```diff
@@ -44,8 +44,8 @@ def __init__(self, quote_type="both"):
                 f"{quote_type} is not a valid quote_type. Specify 'both', 'single', or 'double'",
             )
         self.quote_type = quote_type
-        IN_DOUBLE_QUOTES = r'((^|\W)"(.|\s)*?"(?!\w))'
-        IN_SINGLE_QUOTES = r"((^|\W)'(.|\s)*?'(?!\w))"
+        IN_DOUBLE_QUOTES = r'((^|\W)"(.)*?"(?!\w))'
+        IN_SINGLE_QUOTES = r"((^|\W)'(.)*?'(?!\w))"
         if quote_type == "double":
             self.regex = IN_DOUBLE_QUOTES
         elif quote_type == "single":
@@ -70,7 +70,7 @@ def get_function(self):
         def count_words_in_quotes(text):
             if pd.isnull(text):
                 return pd.NA
-            matches = re.findall(self.regex, text)
+            matches = re.findall(self.regex, text, re.DOTALL)
             count = 0
             for match in matches:
                 matched_phrase = match[0]
```

## Moved from `brief.md`

## Files That May Need Changes

- `featuretools/primitives/standard/transform/natural_language/number_of_words_in_quotes.py`
