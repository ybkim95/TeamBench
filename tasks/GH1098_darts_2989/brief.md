# GH1098_darts_2989: Fix: StaticCovariatesTransformer cols_cat order differing from column order (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest darts/tests/dataprocessing/transformers/test_static_covariates_transformer.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
