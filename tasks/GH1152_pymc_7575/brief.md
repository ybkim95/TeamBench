# GH1152_pymc_7575: Do not mutate Scan inner graph when deriving logprob (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/logprob/test_scan.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
