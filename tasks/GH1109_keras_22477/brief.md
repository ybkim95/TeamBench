# GH1109_keras_22477: [Fix] ConvLSTM1D allows invalid strides/dilation config when built with Keras Input (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest keras/src/layers/rnn/conv_lstm1d_test.py keras/src/layers/rnn/conv_lstm2d_test.py keras/src/layers/rnn/conv_lstm3d_test.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
