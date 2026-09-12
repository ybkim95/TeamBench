# GH1077_spaCy_12623: Support overriding registered functions in configs (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest spacy/tests/serialize/test_serialize_config.py spacy/tests/test_misc.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
