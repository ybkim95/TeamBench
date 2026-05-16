# GH1007_spaCy_13040: Revert "Load the cli module lazily for spacy.info (#12962)" — Full Specification (Planner Only)

## Source
- PR: https://github.com/explosion/spaCy/pull/13040
- Issue: N/A
- Repo: https://github.com/explosion/spaCy

## PR Description

<!--- Provide a general summary of your changes in the title. -->

## Description
<!--- Use this section to describe your changes. If your changes required
testing, include information about the testing environment and the tests you
ran. If your test fixes a bug reported in an issue, don't forget to include the
issue number. If your PR is still a work in progress, that's totally fine – just
include a note to let us know. -->

This reverts commit beda27a91eadd70563dbaffd844d8c9d5e245928.

### Types of change
<!-- What type of change does your PR cover? Is it a bug fix, an enhancement
or new feature, or a change to the documentation? -->

Bug fix.

## Checklist
<!--- Before you submit the PR, go over this checklist and make sure you can
tick off all the boxes. [] -> [x] -->
- [x] I confirm that I have the right to submit this contribution under the project's MIT license.
- [x] I ran the tests, and all new and existing tests passed.
- [x] My changes don't require a change to the documentation, or if they do, I've added all required information.

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

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify the source files listed above (not test files)
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
