# GH1176_keras_21706: Bug fixes with variable handling in `LossScaleOptimizer`. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/keras-team/keras

## PR Description

## overwrite_with_gradient

`overwrite_with_gradient` would be ineffective on JAX in real-world conditions, i.e. within `model.fit`.
    
This is because in the training loop, `stateless_apply` is passed `trainable_variables` as arrays containing the values of the trainable variables, not the variables themselves. Instead, we have to inspect the variables.

## apply with gradients only

`apply(grads)` without the `trainable_variables` argument passed in would not apply anything.
    
This is because the code uses `self._trainable_variables`. But this was an empty array for `LossScaleOptimizer`. This was fixed by adding `super().build(...)`.

## unsupported optimizer arguments
    
Also fail when other arguments from the base optimizer are passed to `LossScaleOptimizer.__init__` since they are not actually supported. They are also no longer returned by `get_config`.

## PR Review Comments

**[user]** on `keras/src/optimizers/loss_scale_optimizer.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

This change accesses a "private" attribute `_trainable_variables` of the inner optimizer. This relies on an internal implementation detail of the `Optimizer` class, which could change in the future and break this code. It also violates the principle of encapsulation.[^1]

A more robust solution would be to expose the trainable variables via a public property on the `BaseOptimizer` class. Since that would require changes in another file, I'll leave it to you to decide on the best path forward.

#### Style Guide References
[^1]: APIs should not deal with internal implementation details. An API should be about the problem it solves, not about how the code works in the background.

**[user]** on `keras/src/optimizers/loss_scale_optimizer.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

Similar to the comment above, accessing the "private" attribute `_trainable_variables` of the inner optimizer makes this code fragile and dependent on implementation details.[^1]

Consider adding a public accessor for these variables in the `BaseOptimizer` class to make this interaction more explicit and maintainable.

#### Style Guide References
[^1]: APIs should not deal with internal implementation details. An API should be about the problem it solves, not about how the code works in the background.

**[user]** on `keras/src/optimizers/loss_scale_optimizer_test.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

The variable name `vars` shadows the built-in Python function `vars()`. It's a good practice to avoid this to prevent confusion and potential bugs. Consider renaming it to something more descriptive like `model_variables` or `trainable_variables` to improve clarity.[^1]

```suggestion
        model_variables = [backend.Variable([1.0, 2.0, 3.0, 4.0])]
        optimizer.build(model_variables)
        optimizer.apply(grads)
        self.assertAllClose(
            model_variables, [[0.5, -1.0, -0.5, 3.0]], rtol=1e-4, atol=1e-4
        )
```

#### Style Guide References
[^1]: Avoid overly generic names and follow Python naming conventions. Shadowing built-in functions is discouraged.

**[user]** on `keras/src/optimizers/loss_scale_optimizer.py`:

Summarizing from our brief in-person discussion:
I don't think we should pull directly from the inner optimizer here.  Instead, we should ensure the loss-scale optimizer has the correct `_trainable_variables` (maybe from calling it's `super().build(...)`).

**[user]** on `keras/src/optimizers/loss_scale_optimizer.py`:

... which would fix this as well.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
