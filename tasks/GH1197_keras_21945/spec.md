# GH1197_keras_21945: Fix handling of symbolic Tensor in RNN — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/keras-team/keras

## PR Description

Per bug reported in https://github.com/keras-team/keras/issues/21942, the batch size check for RNNs added in (withheld: the upstream fix is not part of the task) does not for support symbolic tensors, which happens when we use `ops.shape` ([user] actually mentioned this in the original PR that 21742 was based upon [here]((withheld: the upstream fix is not part of the task)#discussion_r2264087272)). To mitigate this, the `ops.shape` check has been updated to use the `.shape` field. A test has been added based on the original reproduction case - for simplicity, I have made it only for the tensorflow backend.

## PR Review Comments

**[user]** on `keras/src/layers/rnn/gru_test.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

The test name is very long and describes the implementation detail of the bug rather than the behavior being tested. The Keras API design guidelines advise against overly long and specific naming patterns (line 69). A name that is more concise and focused on the behavior would be more aligned with the style guide.

A shorter name like `test_stateful_with_symbolic_batch_size` would be more appropriate as it clearly describes the scenario under test.

```suggestion
    def test_stateful_with_symbolic_batch_size(
```

<details>
<summary>References</summary>

1. The style guide advises to 'Avoid OverlyLongAndSpecificNamingPatterns'. Test names, like argument names, should be intuitive and easy to remember, focusing on the behavior rather than implementation details. <sup>([link](https://github.com/keras-team/keras/blob/master/.gemini/styleguide.md))</sup>
</details>

**[user]** on `keras/src/layers/rnn/rnn.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

While this change fixes the crash with symbolic tensors, it also disables the batch size validation check when a stateful RNN is used within a `tf.function` that has a dynamic batch size in its `input_signature`. By using `sequences.shape[0]`, `actual_batch_size` becomes `None` during tracing, causing the batch size consistency check to be skipped from the traced graph.

This can lead to less clear error messages for users who provide inconsistent batch sizes at runtime, as they will get a cryptic backend error instead of the explicit `ValueError`. This goes against the Keras style guide principle to "Provide detailed feedback messages upon user error" (line 140).

While a fully robust solution might require a new backend op (e.g., `ops.assert_equal`), which is a larger change, it's important to be aware of this trade-off. If this degradation in error reporting is acceptable, the fix is pragmatic. However, preserving the explicit check would be ideal.

<details>
<summary>References</summary>

1. The style guide emphasizes providing detailed and helpful error messages to users. This change, while fixing a crash, weakens an error check in a specific scenario, leading to potentially more confusing errors for the user. <sup>([link](https://github.com/keras-team/keras/blob/master/.gemini/styleguide.md))</sup>
</details>

**[user]** on `keras/src/layers/rnn/gru_test.py`:

Use `@pytest.mark.skipif(` to decorate the test instead of skipping within the test

**[user]** on `keras/src/layers/rnn/gru_test.py`:

Rename `test_stateful_with_dynamic_batch_size`.
Also remove the comma after `self` and let it be a single line.

**[user]** on `keras/src/layers/rnn/gru_test.py`:

I think this test can be re-written this way:

```python
model = models.Sequential([layers.GRU(5, stateful=True)])
model.jit_compile = True

x = np.ones((5, 10, 10), dtype=np.float32)
model(x)

y = model.predict(x, batch_size=2)
self.assertEqual(y.shape, (2, 5))
```

Which I like better because you may be able to run it with other backends since there's no TF specific code. The trick is that `predict` will use a dynamic batch size because it has to.

Let me know if this doesn't work or it doesn't exercise the issue you're fixing.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
