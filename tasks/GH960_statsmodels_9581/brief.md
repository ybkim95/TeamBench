# GH960_statsmodels_9581: BUG: make Binomial family more robust to corner case mu=0 , endog=0 (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest statsmodels/genmod/families/tests/test_family.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
