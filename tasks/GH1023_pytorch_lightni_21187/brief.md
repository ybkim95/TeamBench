# GH1023_pytorch_lightni_21187: Fix edgecase in batch size scaling tuner alg (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/tests_pytorch/tuner/test_scale_batch_size.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
