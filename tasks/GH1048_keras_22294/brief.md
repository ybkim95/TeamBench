# GH1048_keras_22294: fix(progbar): handle target=0 to prevent crash with empty dataset (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest keras/src/utils/progbar_test.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
