# GH1006_spaCy_13068: Fix displacy span stacking (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Files That May Need Changes

- `spacy/displacy/render.py`

## Verification

Run the test suite to confirm your fix:

```
pytest spacy/tests/test_displacy.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
