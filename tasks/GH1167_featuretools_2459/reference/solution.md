# Reference solution — GH1167_featuretools_2459

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1167_featuretools_2459`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1167_featuretools_2459/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/source/release_notes.rst` (modified, +4/-2)
- `featuretools/primitives/standard/transform/natural_language/num_words.py` (modified, +22/-4)
- `featuretools/tests/primitive_tests/natural_language_primitives_tests/test_num_words.py` (added, +76/-0)
- `featuretools/tests/primitive_tests/test_transform_features.py` (modified, +1/-1)

## Diff Summary (What the Fix Changes)

### `featuretools/primitives/standard/transform/natural_language/num_words.py`
```diff
@@ -1,12 +1,21 @@
+import re
+from string import punctuation
+from typing import Optional
+
+import pandas as pd
 from woodwork.column_schema import ColumnSchema
-from woodwork.logical_types import NaturalLanguage
+from woodwork.logical_types import IntegerNullable, NaturalLanguage
 
 from featuretools.primitives.base import TransformPrimitive
+from featuretools.primitives.standard.transform.natural_language.constants import (
+    DELIMITERS,
+)
 from featuretools.utils.gen_utils import Library
 
 
 class NumWords(TransformPrimitive):
-    """Determines the number of words in a string by counting the spaces.
+    """Determines the number of words in a string. Words are sequences of characters
+    delimited by whitespace.
 
     Examples:
         >>> num_words = NumWords()
@@ -19,12 +28,21 @@ class NumWords(TransformPrimitive):
 
     name = "num_words"
     input_types = [ColumnSchema(logical_type=NaturalLanguage)]
-    return_type = ColumnSchema(semantic_tags={"numeric"})
+    return_type = ColumnSchema(logical_type=IntegerNullable, semantic_tags={"numeric"})
     compatibility = [Library.PANDAS, Library.DASK, Library.SPARK]
     description_template = "the number of words in {}"
 
     def get_function(self):
         def word_counter(array):
-            return array.fillna("").str.count(" ") + 1
+            def _get_number_of_words(elem: Optional[str]):
+                """Returns the number of words in given element,
+                or pd.NA given null input"""
+                if pd.isna(elem):
+                    return pd.NA
+                return sum(
+                    1 for word in re.split(DELIMITERS, elem) if word.strip(punctuation)
+                )
+
+            return array.apply(_get_number_of_words)
 
         return word_counter
```

## Moved from `brief.md`

## Files That May Need Changes

- `featuretools/primitives/standard/transform/natural_language/num_words.py`
