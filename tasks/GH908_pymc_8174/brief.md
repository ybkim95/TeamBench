# GH908_pymc_8174: Fix broadcast check on log_jac_det (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/distributions/test_transform.py tests/logprob/test_transform_value.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
