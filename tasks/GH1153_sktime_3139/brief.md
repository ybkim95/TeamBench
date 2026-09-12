# GH1153_sktime_3139: [MNT] temporarily exclude `RandomShapeletTransform` from tests (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest sktime/tests/_config.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
