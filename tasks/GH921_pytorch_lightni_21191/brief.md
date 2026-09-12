# GH921_pytorch_lightni_21191: Fix missing reset when pruning with lottery ticket hypothesis (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/tests_pytorch/callbacks/test_pruning.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
