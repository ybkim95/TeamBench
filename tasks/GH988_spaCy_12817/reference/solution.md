# Reference solution — GH988_spaCy_12817

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH988_spaCy_12817`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH988_spaCy_12817/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `spacy/displacy/render.py` (modified, +1/-2)
- `spacy/tests/test_displacy.py` (modified, +19/-0)

## Diff Summary (What the Fix Changes)

### `spacy/displacy/render.py`
```diff
@@ -1,4 +1,3 @@
-import itertools
 import uuid
 from typing import Any, Dict, List, Optional, Tuple, Union
 
@@ -218,7 +217,7 @@ def _render_markup(self, per_token_info: List[Dict[str, Any]]) -> str:
                     + (self.offset_step * (len(entities) - 1))
                 )
                 markup += self.span_template.format(
-                    text=token["text"],
+                    text=escape_html(token["text"]),
                     span_slices=slices,
                     span_starts=starts,
                     total_height=total_height,
```

## Moved from `brief.md`

## Files That May Need Changes

- `spacy/displacy/render.py`
