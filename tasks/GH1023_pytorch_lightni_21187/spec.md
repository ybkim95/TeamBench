# GH1023_pytorch_lightni_21187: Fix edgecase in batch size scaling tuner alg — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/Lightning-AI/pytorch-lightning/issues/18426
- Repo: https://github.com/Lightning-AI/pytorch-lightning

## Issue Description

### Bug description

When we instruct a tuner to try several batch_size values with power scaling in `scale_batch_size`, and all tested values pass, `scale_batch_size` should return the largest tested value. Instead, it returns an even larger number, without testing that it works as a batch_size. As a result, this may lead to OOMs during training.

For example:

We call a tuner's `scale_batch_size` method with arguments `max_trials=3`, and `init_val=2`. Suppose we call it on a model that works well with `batch_size=8`, but fails with `batch_size=16`. 

In that case, the tuner should try values 2, 4, 8, and if all trials are successful, return 8. 
Instead, it tries values 2, 4, 8, and returns 16 without trying it.

I wrote a minimal reproducible example for this.
 

### What version are you seeing the problem on?

v2.0

### How to reproduce the bug

```python
import lightning.pytorch as pl
import torch
import torch.utils.data
from typing import Any

from lightning.pytorch.utilities.types import TRAIN_DATALOADERS, STEP_OUTPUT
from lightning.pytorch.tuner import Tuner


class ToyModel(pl.LightningModule):
    def __init__(self):
        super().__init__()
        self.layer = torch.nn.Linear(5, 10)

    def forward(self, toy_variable: torch.Tensor) -> Any:
        return self.layer(toy_variable)

    def training_step(self, batch: torch.Tensor) -> STEP_OUTPUT:
        return self.layer(batch).sum()

    def configure_optimizers(self) -> Any:
        return torch.optim.Adam(params=self.parameters())


class ToyDataset(torch.utils.data.Dataset):
    def __init__(self, throw_error: bool):
        super().__init__()
        self.throw_error = throw_error

    def __len__(self):
        return 100

    def __getitem__(self, item):
        if self.throw_error:
            raise RuntimeError("CUDA error: out of memory")
        else:
            return torch.randn((5,))


class ToyDatamodule(pl.LightningDataModule):
    def __init__(self):
        super().__init__()
        self.batch_size = 1

    def train_dataloader(self) -> TRAIN_DATALOADERS:
        return torch.utils.data.DataLoader(ToyDataset(throw_error=(self.batch_size >= 16)))


def main():
    trainer = pl.Trainer()
    tuner = Tuner(trainer=trainer)

    model: pl.LightningModule = ToyModel()
    toy_datamodule: pl.LightningDataModule = ToyDatamodule()

    batch_size: int = tuner.scale_batch_size(
        model=model,
        datamodule=toy_datamodule,
        method="fit",
        steps_per_trial=3,
        max_trials=25,
    )
    print(f"This batch_size is {batch_size}, expected 8 (because 16 should fail)")

    batch_size: int = tuner.scale_batch_size(
        model=model,
        datamodule=toy_datamodule,
        method="fit",
        steps_per_trial=3,
        max_trials=3,
    )
    print(f"This batch_size is {batch_size}, expected 8 (because 16 should fail)")


if __name__ == '__main__':
    main()
```


The first call of `scale_batch_size` results in the following (correct) output:

```
`Trainer.fit` stopped: `max_steps=3` reached.
Batch size 2 succeeded, trying batch size 4
`Trainer.fit` stopped: `max_steps=3` reached.
Batch size 4 succeeded, trying batch size 8
`Trainer.fit` stopped: `max_steps=3` reached.
Batch size 8 succeeded, trying batch size 16
Batch size 16 failed, trying batch size 8
This batch_size is 8, expected 8 (because 16 should fail)
```

The second call results in the following (incorrect) output:

```
`Trainer.fit` stopped: `max_steps=3` reached.
Batch size 2 succeeded, trying batch size 4
`Trainer.fit` stopped: `max_steps=3` reached.
Batch size 4 succeeded, trying batch size 8
`Trainer.fit` stopped: `max_steps=3` reached.
Batch size 8 succeeded, trying batch size 16
Finished batch size finder, will continue with full run using batch size 16
This batch_size is 16, expected 8 (because 16 should fail)
```

### Error messages and logs

```
# Error messages and logs here please
```


### Environment

<details>
  <summary>Current environment</summary>

```
#- Lightning Component (e.g. Trainer, LightningModule, LightningApp, LightningWork, LightningFlow):
#- PyTorch Lightning Version (e.g., 1.5.0):
#- Lightning App Version (e.g., 0.5.2):
#- PyTorch Version (e.g., 2.0):
#- Python version (e.g., 3.9):
#- OS (e.g., Linux):
#- CUDA/cuDNN version:
#- GPU models and configuration:
#- How you installed Lightning(`conda`, `pip`, source):
#- Running environment of LightningApp (e.g. local, cloud):
```

</details>


### More info

_No response_

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
