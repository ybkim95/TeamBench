# GH865_pytorch_lightni_6877: [Fix] Ensure we set the eval/train flag correctly on accelerator model  — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/Lightning-AI/pytorch-lightning/issues/6876
- Repo: https://github.com/Lightning-AI/pytorch-lightning

## Issue Description

## 🐛 Bug

When validation/training is used (as default with the boring model) sharded crashes. This is because internally SDP relies on knowing the training state of the model, and when we run the validation sanity check, we do not set the eval mode correctly on the SDP model itself, so it waits for grads to be reduced since the module is in `train` mode.

```python
import os

import torch
from torch.utils.data import Dataset

from pytorch_lightning import LightningModule, Trainer


class RandomDataset(Dataset):
    """
    >>> RandomDataset(size=10, length=20)  # doctest: +ELLIPSIS
    <...bug_report_model.RandomDataset object at ...>
    """

    def __init__(self, size, length):
        self.len = length
        self.data = torch.randn(length, size)

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return self.len


class BoringModel(LightningModule):
    """
    >>> BoringModel()  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    BoringModel(
      (layer): Linear(...)
    )
    """

    def __init__(self):
        """
        Testing PL Module

        Use as follows:
        - subclass
        - modify the behavior for what you want

        class TestModel(BaseTestModel):
            def training_step(...):
                # do your own thing

        or:

        model = BaseTestModel()
        model.training_epoch_end = None

        """
        super().__init__()
        self.layer = torch.nn.Linear(32, 2)

    def forward(self, x):
        return self.layer(x)

    def loss(self, batch, prediction):
        # An arbitrary loss to have a loss that updates the model weights during `Trainer.fit` calls
        return torch.nn.functional.mse_loss(prediction, torch.ones_like(prediction))

    def step(self, x):
        x = self.layer(x)
        out = torch.nn.functional.mse_loss(x, torch.ones_like(x))
        return out

    def training_step(self, batch, batch_idx):
        output = self.layer(batch)
        loss = self.loss(batch, output)
        return {"loss": loss}

    def validation_step(self, batch, batch_idx):
        output = self.layer(batch)
        loss = self.loss(batch, output)
        return {"x": loss}

    def test_step(self, batch, batch_idx):
        output = self.layer(batch)
        loss = self.loss(batch, output)
        return {"y": loss}

    def configure_optimizers(self):
        optimizer = torch.optim.SGD(self.layer.parameters(), lr=0.1)
        lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1)
        return [optimizer], [lr_scheduler]


def test_run():
    # fake data
    train_data = torch.utils.data.DataLoader(RandomDataset(32, 64))
    val_data = torch.utils.data.DataLoader(RandomDataset(32, 64))
    test_data = torch.utils.data.DataLoader(RandomDataset(32, 64))

    # model
    model = BoringModel()
    trainer = Trainer(
        default_root_dir=os.getcwd(),
        limit_train_batches=1,
        limit_val_batches=1,
        max_epochs=1,
        plugins='ddp_sharded',
        gpus=1,
        weights_summary=None,
    )
    trainer.fit(model, train_data, val_data)
    trainer.test(test_dataloaders=test_data)


if __name__ == '__main__':
    test_run()
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

1 workaround is setting `num_sanity_val_steps=0` but that's very much a short-term fix

## PR Review Comments

**[user]** on `pytorch_lightning/trainer/trainer.py`:

careful, right above here we have a special hook `self.evaluation_loop.on_evaluation_model_eval`
we probably don't want to override this behaviour if the user implements this hook
same for the other places (e.g. predict)
confidence on this statement: ~60%

**[user]** on `pytorch_lightning/trainer/trainer.py`:

Same here.

**[user]** on `pytorch_lightning/trainer/trainer.py`:

```suggestion
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
