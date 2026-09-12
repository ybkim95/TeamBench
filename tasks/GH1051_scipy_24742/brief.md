# GH1051_scipy_24742: BUG: stats.linregress return NaN in n=2 cases (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest scipy/stats/tests/test_stats.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
