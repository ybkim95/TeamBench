# GH1197_keras_21945: Fix handling of symbolic Tensor in RNN (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest keras/src/layers/rnn/gru_test.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
