# GH1128_FLAML_1475: Fix: Preserve FLAML_sample_size in best_config_per_estimator (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest test/automl/test_multiclass.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
