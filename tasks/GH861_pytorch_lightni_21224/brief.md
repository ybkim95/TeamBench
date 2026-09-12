# GH861_pytorch_lightni_21224: Bugfix for `BackboneFinetuning` + `LearningRateFinder` (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/tests_pytorch/tuner/test_lr_finder.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
