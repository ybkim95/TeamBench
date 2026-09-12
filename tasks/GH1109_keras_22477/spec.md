# GH1109_keras_22477: [Fix] ConvLSTM1D allows invalid strides/dilation config when built with Keras Input — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/keras-team/keras

## PR Description

Fixes issues: #22474 #22475 #22476

Root cause: ConvLSTMCell normalized strides and dilation_rate but didn’t validate their incompatible combination (> 1 together).
So, symbolic layers.Input builds didn’t raise errors

Solution: Added validation in ```ConvLSTMCell.__init__```to raise ValueError when both are > 1.
Also added to regression tests to ensure symbolic builds now correctly fail across ConvLSTM1D/2D/3D.

## PR Review Comments

**[user]** on `keras/src/layers/rnn/conv_lstm.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

According to the Keras API design guidelines, error messages should be actionable and tell the user how to fix the issue. The current message implies the fix, but we can make it more explicit to better guide the user.

```suggestion
            raise ValueError(
                "Specifying `strides > 1` is not compatible with "
                "`dilation_rate > 1`. Please provide `strides=1` or "
                "`dilation_rate=1`. "
                f"Received: strides={self.strides} and "
                f"dilation_rate={self.dilation_rate}"
            )
```

<details>
<summary>References</summary>

1. The Keras style guide (lines 139-143, 192-205) states that error messages should be actionable and tell the user how to fix the issue. The suggested change makes the error message more explicit about the required fix. <sup>([link](https://github.com/keras-team/keras/blob/master/.gemini/styleguide.md))</sup>
</details>

**[user]** on `keras/src/layers/rnn/conv_lstm1d_test.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

This regular expression should be updated to match the improved error message suggested for `conv_lstm.py`.

```suggestion
            r"Specifying `strides > 1` is not compatible with "
            r"`dilation_rate > 1`",
```

**[user]** on `keras/src/layers/rnn/conv_lstm2d_test.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

This regular expression should be updated to match the improved error message suggested for `conv_lstm.py`.

```suggestion
            r"Specifying `strides > 1` is not compatible with "
            r"`dilation_rate > 1`",
```

**[user]** on `keras/src/layers/rnn/conv_lstm3d_test.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

This regular expression should be updated to match the improved error message suggested for `conv_lstm.py`.

```suggestion
            r"Specifying `strides > 1` is not compatible with "
            r"`dilation_rate > 1`",
```

**[user]** on `keras/src/layers/rnn/conv_lstm1d_test.py`:

Remove `@pytest.mark.requires_trainable_backend` in all 3 tests, it's unrelated.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
