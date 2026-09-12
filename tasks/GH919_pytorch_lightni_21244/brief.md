# GH919_pytorch_lightni_21244: Fix `last.ckpt` only being saved when another checkpoint has been created (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/tests_pytorch/checkpointing/test_model_checkpoint.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
