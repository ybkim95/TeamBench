# GH1083_sktime_3207: [BUG] skip check for no. estimators in contracted classifiers (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest sktime/classification/dictionary_based/tests/test_tde.py sktime/classification/interval_based/tests/test_drcif.py sktime/classification/shapelet_based/tests/test_stc.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
