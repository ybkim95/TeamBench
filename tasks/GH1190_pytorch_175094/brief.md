# GH1190_pytorch_175094: Revert "[fix] DISABLED test_index (__main__.DistTensorOpsTest) (#172373)" (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest test/distributed/tensor/test_tensor_ops.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
