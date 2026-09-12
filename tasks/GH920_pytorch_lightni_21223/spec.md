# GH920_pytorch_lightni_21223: Fix logged sparsity calculation in `ModelPruning` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/Lightning-AI/pytorch-lightning/issues/13595
- Repo: https://github.com/Lightning-AI/pytorch-lightning

## Issue Description

## 🐛 Bug

<!-- A clear and concise description of the bug. -->
When using `ModelPruning` callback with verbosity level in {1,2}, the logged sparsity would be wrong when there are layers with multiple parameters to be pruned.
For example, when we add a `ModelPruning(amount=0.2)` callback to the [BoringModel Colab link](https://colab.research.google.com/github/Lightning-AI/lightning/blob/master/examples/pl_bug_report/bug_report_model.ipynb), we would get overall sparsity logged around 0.1 instead of 0.2:
```
Applied `L1Unstructured`. Pruned: 0/132 (0.00%) -> 13/132 (9.85%)
Applied `L1Unstructured` to `Linear(in_features=32, out_features=2, bias=True).weight` with amount=0.2. Pruned: 0 (0.00%) -> 13 (20.31%)
Applied `L1Unstructured` to `Linear(in_features=32, out_features=2, bias=True).bias` with amount=0.2. Pruned: 0 (0.00%) -> 0 (0.00%)
```

The problem is mainly due to L346 in the following code, where there might have layers counted multiple times:
https://github.com/Lightning-AI/lightning/blob/b59f80224843886459d54c828325683d770da746/src/pytorch_lightning/callbacks/pruning.py#L343-L353
Can be fixed easily by:
```python
# count from prev/curr should be the same
total_params = sum(params for _, params in prev)
```

### To Reproduce

<!--
Please reproduce using the BoringModel!

You can use the following Colab link:
https://colab.research.google.com/github/Lightning-AI/lightning/blob/master/examples/pl_bug_report/bug_report_model.ipynb
IMPORTANT: has to be public.

or this simple template:
https://github.com/Lightning-AI/lightning/blob/master/examples/pl_bug_report/bug_report_model.py

If you could not reproduce using the BoringModel and still think there's a bug, please post here
but remember, bugs with code are fixed faster!
-->
https://gist.github.com/SungFeng-Huang/52d676869ad4e8a4a00ac3e29437ecdd

<details>

<summary>Reproducible python code</summary>

```python
import os

import torch
from torch.utils.data import DataLoader, Dataset

from lightning import LightningModule, Trainer


class RandomDataset(Dataset):
    def __init__(self, size, num_samples):
        self.len = num_samples
        self.data = torch.randn(num_samples, size)

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return self.len


num_samples = 10000

class BoringModel(LightningModule):
    def __init__(self):
        super().__init__()
        self.layer = torch.nn.Linear(32, 2)

    def forward(self, x):
        return self.layer(x)

    def training_step(self, batch, batch_idx):
        loss = self(batch).sum()
        self.log("train_loss", loss)
        return {"loss": loss}

    def validation_step(self, batch, batch_idx):
        loss = self(batch).sum()
        self.log("valid_loss", loss)

    def test_step(self, batch, batch_idx):
        loss = self(batch).sum()
        self.log("test_loss", loss)

    def configure_optimizers(self):
        return torch.optim.SGD(self.layer.parameters(), lr=0.1)

from lightning.pytorch.callbacks import ModelPruning


def run():
    train_data = DataLoader(RandomDataset(32, 64), batch_size=2, num_workers = 2, persistent_workers = True)
    val_data = DataLoader(RandomDataset(32, 64), batch_size=2, num_workers = 2, persistent_workers = True)
    test_data = DataLoader(RandomDataset(32, 64), batch_size=2, num_workers = 2, persistent_workers = True)

    pruning = ModelPruning(
        pruning_fn="l1_unstructured",
        parameters_to_prune=None,
        use_global_unstructured=True,
        amount=0.2,
        apply_pruning=True,
        use_lottery_ticket_hypothesis=True,
        resample_parameters=False,
        verbose=2,
        prune_on_train_epoch_end=True,
    )

    model = BoringModel()
    trainer = Trainer(
        default_root_dir=os.getcwd(),
        limit_train_batches=1,
        limit_val_batches=1,
        limit_test_batches=1,
        num_sanity_val_steps=0,
        max_epochs=1,
        enable_model_summary=False,
        callbacks=[pruning],
        enable_progress_bar=False,
    )
    trainer.fit(model, train_dataloaders=train_data, val_dataloaders=val_data)
    trainer.test(model, dataloaders=test_data)


if __name__ == "__main__":
    run()
```

</details>

### Expected behavior

<!-- FILL IN -->
Get sparsity logged around 0.2 instead of 0.1:
```
Applied `L1Unstructured`. Pruned: 0/132 (0.00%) -> 13/66 (19.70%)
Applied `L1Unstructured` to `Linear(in_features=32, out_features=2, bias=True).weight` with amount=0.2. Pruned: 0 (0.00%) -> 13 (20.31%)
Applied `L1Unstructured` to `Linear(in_features=32, out_features=2, bias=True).bias` with amount=0.2. Pruned: 0 (0.00%) -> 0 (0.00%)
```

### Environment

<!--
Please copy and paste the output from our environment collection script:
https://raw.githubusercontent.com/Lightning-AI/lightning/master/requirements/collect_env_details.py
(For security purposes, please check the contents of the script before running it)

You can get the script and run it with:
```bash
wget https://raw.githubusercontent.com/Lightning-AI/lightning/master/requirements/collect_env_details.py
python collect_env_details.py
```

You can also fill out the list below manually.
-->

* CUDA:
	- GPU:
		- Tesla T4
	- available:         True
	- version:           11.3
* Packages:
	- numpy:             1.21.6
	- pyTorch_debug:     False
	- pyTorch_version:   1.11.0+cu113
	- pytorch-lightning: 1.6.4
	- tqdm:              4.64.0
* System:
	- OS:                Linux
	- architecture:
		- 64bit
		- 
	- processor:         x86_64
	- python:            3.7.13
	- version:           #1 SMP Sun Apr 24 10:03:06 PDT 2022

<!--
- PyTorch Lightning Version (e.g., 1.5.0):
- PyTorch Version (e.g., 1.10):
- Python version (e.g., 3.9):
- OS (e.g., Linux):
- CUDA/cuDNN version:
- GPU models and configuration:
- How you installed PyTorch (`conda`, `pip`, source):
- If compiling from source, the output of `torch.__config__.show()`:
- Any other relevant information:
-->

### Additional context

<!-- Add any other context about the problem here. -->


cc [user] [user]

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Sounds good to me. Feel free to open a PR with the fix and a test!

### Comment 2 ([user]):

**Confirming behavior:**

The callback counts parameters twice for the same module (once for `weight`, once for `bias`), which explains the incorrect sparsity. I confirmed the behavior: both parameters reference the same layer object:

```python
layer=Linear(in_features=32, out_features=20, bias=True); name='weight'
        layer.parameters()=<generator object Module.parameters at 0x1496dc580>


layer=Linear(in_features=32, out_features=20, bias=True); name='bias'
        layer.parameters()=<generator object Module.parameters at 0x1496dc580>
```

and `layer.parameters()` yields the same generator each time.

The fix you suggested (`total_params = sum(params for _, params in prev)`) makes sense and aligns with the intended logic.

Thanks again for the clear repro and detailed report. This was really helpful!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
