# GH1110_keras_22439: Fix: Conv1DTranspose: Invalid Symbolic Shape + Runtime Crash When output_padding ≥ strides (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest keras/src/layers/convolutional/conv_transpose_test.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
