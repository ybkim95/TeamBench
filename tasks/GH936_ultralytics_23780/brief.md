# GH936_ultralytics_23780: Fix FP16 inference crash from TinyViT cached bias dtype mismatch (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/test_cuda.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
