# GH1073_spaCy_13249: `TextCatParametricAttention.v1`: set key transform dimensions (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest spacy/tests/pipeline/test_textcat.py spacy/tests/tok2vec.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
