# GH1007_spaCy_13040: Revert "Load the cli module lazily for spacy.info (#12962)" (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Files That May Need Changes

- `spacy/__init__.py`

## Verification

Run the test suite to confirm your fix:

```
pytest spacy/tests/test_cli.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
