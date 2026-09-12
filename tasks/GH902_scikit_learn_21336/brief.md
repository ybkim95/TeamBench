# GH902_scikit_learn_21336: FIX Prevents segfault in SVC when internals are altered (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest sklearn/svm/tests/test_svm.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
