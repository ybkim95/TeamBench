# GH981_statsmodels_9468: BUG: svar, A,B dtype, one parameter score shape, closes #9302 (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest statsmodels/tsa/vector_ar/tests/test_svar.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
