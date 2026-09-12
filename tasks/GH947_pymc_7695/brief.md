# GH947_pymc_7695: Fix bug when reusing jax logp for initial point generation (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/sampling/test_jax.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
