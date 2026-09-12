# GH860_pytorch_lightni_21396: Fix `StochasticWeightAveraging`  with infinite epochs (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/tests_pytorch/callbacks/test_stochastic_weight_avg.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
