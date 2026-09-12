# GH860_pytorch_lightni_21396: Fix `StochasticWeightAveraging`  with infinite epochs — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/Lightning-AI/pytorch-lightning/issues/21347
- Repo: https://github.com/Lightning-AI/pytorch-lightning

## Issue Description

### Bug description

When training `ResNet18`, which contains a `BatchNorm2d` layer and setting `max_epochs` to `-1` for infinite training, the `trainer.fit` ends early due to increment of `max_epochs` in `StochasticWeightAveraging`.

The trainer prints the following message after the sanity check and discontinues the training.
```
`Trainer.fit` stopped: `max_epochs=0` reached.
```

The logged `max_epochs` is different from our configuration, which clearly shows an unexpected increment.

---

The following condition is met when the trained model contains `_BatchNorm` in [stochastic_weight_avg.py](https://github.com/Lightning-AI/pytorch-lightning/blob/233794816d4463628eba054026386004f15cff56/src/lightning/pytorch/callbacks/stochastic_weight_avg.py#L170-L174)
```python
        self._max_epochs = trainer.max_epochs
        if self._model_contains_batch_norm:
            # virtually increase max_epochs to perform batch norm update on latest epoch.
            assert trainer.fit_loop.max_epochs is not None
            trainer.fit_loop.max_epochs += 1
```

After the `max_epochs` is set to `0`, the fit loop stops when checking the following condition in [fit_loop.py](https://github.com/Lightning-AI/pytorch-lightning/blob/233794816d4463628eba054026386004f15cff56/src/lightning/pytorch/loops/fit_loop.py#L188-L193)
```python
        # `processed` is increased before `on_train_epoch_end`, the hook where checkpoints are typically saved.
        # we use it here because the checkpoint data won't have `completed` increased yet
        assert isinstance(self.max_epochs, int)
        stop_epochs = _is_max_limit_reached(self.epoch_progress.current.processed, self.max_epochs)
        if stop_epochs:
            # in case they are not equal, override so `trainer.current_epoch` has the expected value
            self.epoch_progress.current.completed = self.epoch_progress.current.processed
            rank_zero_info(f"`Trainer.fit` stopped: `max_epochs={self.max_epochs!r}` reached.")
            return True
```

### What version are you seeing the problem on?

v2.5

### Reproduced in studio

_No response_

### How to reproduce the bug

```python

```

### Error messages and logs

```
# Error messages and logs here please
```


### Environment

<details>
  <summary>Current environment</summary>

```
#- PyTorch Lightning Version (e.g., 2.5.0): 2.5.1
#- PyTorch Version (e.g., 2.5): 2.6.0
#- Python version (e.g., 3.12): 3.12.10
#- OS (e.g., Linux): Linux
#- CUDA/cuDNN version: 11.8
#- GPU models and configuration:
#- How you installed Lightning(`conda`, `pip`, source): poetry
```

</details>


### More info

_No response_

cc [user] [user] [user]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
