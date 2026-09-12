# Reference solution — GH1007_spaCy_13040

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1007_spaCy_13040`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1007_spaCy_13040/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `spacy/__init__.py` (modified, +1/-6)
- `spacy/tests/test_cli.py` (modified, +0/-4)

## Diff Summary (What the Fix Changes)

### `spacy/__init__.py`
```diff
@@ -13,6 +13,7 @@
 from . import pipeline  # noqa: F401
 from . import util
 from .about import __version__  # noqa: F401
+from .cli.info import info  # noqa: F401
 from .errors import Errors
 from .glossary import explain  # noqa: F401
 from .language import Language
@@ -76,9 +77,3 @@ def blank(
     # We should accept both dot notation and nested dict here for consistency
     config = util.dot_to_dict(config)
     return LangClass.from_config(config, vocab=vocab, meta=meta)
-
-
-def info(*args, **kwargs):
-    from .cli.info import info as cli_info
-
-    return cli_info(*args, **kwargs)
```

## Moved from `brief.md`

## Files That May Need Changes

- `spacy/__init__.py`
