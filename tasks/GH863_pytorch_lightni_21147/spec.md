# GH863_pytorch_lightni_21147: Fix TQDM progress bar showing the wrong total when using a finite and iterable dataloader — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/Lightning-AI/pytorch-lightning/issues/20695
- Repo: https://github.com/Lightning-AI/pytorch-lightning

## Issue Description

### Bug description

When using multiple data loaders—some based on standard datasets with a known length and others on iterable datasets with an undefined length—the progress bar will display the total batches from the dataset-based loader rather than showing “?” for the iterable loader.

### What version are you seeing the problem on?

v2.1

### How to reproduce the bug

```python
import pytorch_lightning as pl
import torch
from torch.utils.data import Dataset, DataLoader, IterableDataset

# 1. Create a simple dummy Dataset
class DummyDataset(Dataset):
    def __init__(self, length=1000):
        super().__init__()
        self.length = length
        # for example, 10 features per sample
        self.data = torch.randn(length, 10)
        # binary classification target [0/1]
        self.targets = torch.randint(0, 2, (length,))

    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        x = self.data[idx]
        y = self.targets[idx]
        return x, y
    
class DummyIterDataset(IterableDataset):
    def __init__(self, length=10000):
        super().__init__()
        self.length = length
        # for example, 10 features per sample
        self.data = torch.randn(length, 10)
        # binary classification target [0/1]
        self.targets = torch.randint(0, 2, (length,))

    def __iter__(self):
        for idx in range(self.length):
            x = self.data[idx]
            y = self.targets[idx]
            yield x, y

# 2. Implement the LightningDataModule
class DummyDataModule(pl.LightningDataModule):
    def __init__(self, batch_size=32):
        super().__init__()
        self.batch_size = batch_size
    
    def setup(self, stage=None):
        # here you can split training/validation/test data 
        # but we will use the same dummy dataset for all
        self.train_dataset = DummyDataset()
        self.val_dataset   = DummyDataset()
        self.val_dataset_1 = DummyIterDataset()
        self.test_dataset  = DummyDataset()
    
    def train_dataloader(self):
        return DataLoader(self.train_dataset, batch_size=self.batch_size)
    
    def val_dataloader(self):
        return [DataLoader(self.val_dataset, batch_size=self.batch_size), DataLoader(self.val_dataset_1, batch_size=self.batch_size)]
    
    def test_dataloader(self):
        return DataLoader(self.test_dataset, batch_size=self.batch_size)

# 3. Define a minimal LightningModule
class DummyModel(pl.LightningModule):
    def __init__(self):
        super().__init__()
        # a single linear layer to map 10 features -> 2 classes
        self.layer = torch.nn.Linear(10, 2)
    
    def forward(self, x):
        return self.layer(x)
    
    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = torch.nn.functional.cross_entropy(logits, y)
        self.log('train_loss', loss)
        return loss
    
    def validation_step(self, batch, batch_idx, dataloader_idx):
        x, y = batch
        logits = self(x)
        loss = torch.nn.functional.cross_entropy(logits, y)
        self.log('val_loss', loss)
        print(batch_idx)
        return loss
    
    # define optimizer
    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=1e-3)

# 4. Instantiate the DataModule and Model, then simulate trainer fit
def run_dummy_training():
    datamodule = DummyDataModule(batch_size=32)
    model = DummyModel()
    trainer = pl.Trainer(devices=1, max_epochs=5, enable_checkpointing=False)
    trainer.validate(model, datamodule=datamodule)

if __name__ == "__main__":
    run_dummy_training()
```

### Error messages and logs

```
Validation DataLoader 0:   0%|                                                                                                             | 0/32 [00:00<?, ?it/s]0
Validation DataLoader 0:   3%|███▏                                                                                                 | 1/32 [00:00<00:02, 14.33it/s]1
Validation DataLoader 0:   6%|██████▎                                                                                              | 2/32 [00:00<00:01, 28.18it/s]2
Validation DataLoader 0:   9%|█████████▍                                                                                           | 3/32 [00:00<00:00, 41.74it/s]3
Validation DataLoader 0:  12%|████████████▋                                                                                        | 4/32 [00:00<00:00, 55.05it/s]4
Validation DataLoader 0:  16%|███████████████▊                                                                                     | 5/32 [00:00<00:00, 68.07it/s]5
Validation DataLoader 0:  19%|██████████████████▉                                                                                  | 6/32 [00:00<00:00, 80.79it/s]6
Validation DataLoader 0:  22%|██████████████████████                                                                               | 7/32 [00:00<00:00, 93.26it/s]7
Validation DataLoader 0:  25%|█████████████████████████                                                                           | 8/32 [00:00<00:00, 105.47it/s]8
Validation DataLoader 0:  28%|████████████████████████████▏                                                                       | 9/32 [00:00<00:00, 117.43it/s]9
Validation DataLoader 0:  31%|██████████████████████████████▉                                                                    | 10/32 [00:00<00:00, 129.15it/s]10
Validation DataLoader 0:  34%|██████████████████████████████████                                                                 | 11/32 [00:00<00:00, 140.62it/s]11
Validation DataLoader 0:  38%|█████████████████████████████████████▏                                                             | 12/32 [00:00<00:00, 151.86it/s]12
Validation DataLoader 0:  41%|████████████████████████████████████████▏                                                          | 13/32 [00:00<00:00, 162.89it/s]13
Validation DataLoader 0:  44%|███████████████████████████████████████████▎                                                       | 14/32 [00:00<00:00, 173.70it/s]14
Validation DataLoader 0:  47%|██████████████████████████████████████████████▍                                                    | 15/32 [00:00<00:00, 184.29it/s]15
Validation DataLoader 0:  50%|█████████████████████████████████████████████████▌                                                 | 16/32 [00:00<00:00, 194.67it/s]16
Validation DataLoader 0:  53%|████████████████████████████████████████████████████▌                                              | 17/32 [00:00<00:00, 204.86it/s]17
Validation DataLoader 0:  56%|███████████████████████████████████████████████████████▋                                           | 18/32 [00:00<00:00, 214.86it/s]18
Validation DataLoader 0:  59%|██████████████████████████████████████████████████████████▊                                        | 19/32 [00:00<00:00, 224.68it/s]19
Validation DataLoader 0:  62%|█████████████████████████████████████████████████████████████▉                                     | 20/32 [00:00<00:00, 234.31it/s]20
Validation DataLoader 0:  66%|████████████████████████████████████████████████████████████████▉                                  | 21/32 [00:00<00:00, 243.73it/s]21
Validation DataLoader 0:  69%|████████████████████████████████████████████████████████████████████                               | 22/32 [00:00<00:00, 253.03it/s]22
Validation DataLoader 0:  72%|███████████████████████████████████████████████████████████████████████▏                           | 23/32 [00:00<00:00, 262.14it/s]23
Validation DataLoader 0:  75%|██████████████████████████████████████████████████████████████████████████▎                        | 24/32 [00:00<00:00, 271.08it/s]24
Validation DataLoader 0:  78%|█████████████████████████████████████████████████████████████████████████████▎                     | 25/32 [00:00<00:00, 279.87it/s]25
Validation DataLoader 0:  81%|████████████████████████████████████████████████████████████████████████████████▍                  | 26/32 [00:00<00:00, 288.45it/s]26
Validation DataLoader 0:  84%|███████████████████████████████████████████████████████████████████████████████████▌               | 27/32 [00:00<00:00, 296.94it/s]27
Validation DataLoader 0:  88%|██████████████████████████████████████████████████████████████████████████████████████▋            | 28/32 [00:00<00:00, 305.27it/s]28
Validation DataLoader 0:  91%|█████████████████████████████████████████████████████████████████████████████████████████▋         | 29/32 [00:00<00:00, 313.46it/s]29
Validation DataLoader 0:  94%|████████████████████████████████████████████████████████████████████████████████████████████▊      | 30/32 [00:00<00:00, 321.52it/s]30
Validation DataLoader 0:  97%|███████████████████████████████████████████████████████████████████████████████████████████████▉   | 31/32 [00:00<00:00, 329.68it/s]31
Validation DataLoader 1:   0%|                                                                                                             | 0/32 [00:00<?, ?it/s]0
Validation DataLoader 1:   3%|███▏                                                                                                | 1/32 [00:00<00:00, 873.27it/s]1
Validation DataLoader 1:   6%|██████▏                                                                                            | 2/32 [00:00<00:00, 1007.88it/s]2
Validation DataLoader 1:   9%|█████████▎                                                                                         | 3/32 [00:00<00:00, 1077.49it/s]3
Validation DataLoader 1:  12%|████████████▍                                                                                      | 4/32 [00:00<00:00, 1118.26it/s]4
Validation DataLoader 1:  16%|███████████████▍                                                                                   | 5/32 [00:00<00:00, 1142.80it/s]5
Validation DataLoader 1:  19%|██████████████████▌                                                                                | 6/32 [00:00<00:00, 1161.37it/s]6
Validation DataLoader 1:  22%|█████████████████████▋                                                                             | 7/32 [00:00<00:00, 1175.20it/s]7
Validation DataLoader 1:  25%|████████████████████████▊                                                                          | 8/32 [00:00<00:00, 1184.16it/s]8
Validation DataLoader 1:  28%|███████████████████████████▊                                                                       | 9/32 [00:00<00:00, 1192.43it/s]9
Validation DataLoader 1:  31%|██████████████████████████████▋                                                                   | 10/32 [00:00<00:00, 1199.13it/s]10
Validation DataLoader 1:  34%|█████████████████████████████████▋                                                                | 11/32 [00:00<00:00, 1204.85it/s]11
Validation DataLoader 1:  38%|████████████████████████████████████▊                                                             | 12/32 [00:00<00:00, 1209.23it/s]12
Validation DataLoader 1:  41%|███████████████████████████████████████▊                                                          | 13/32 [00:00<00:00, 1213.06it/s]13
Validation DataLoader 1:  44%|██████████████████████████████████████████▉                                                       | 14/32 [00:00<00:00, 1215.29it/s]14
Validation DataLoader 1:  47%|█████████████████████████████████████████████▉                                                    | 15/32 [00:00<00:00, 1218.26it/s]15
Validation DataLoader 1:  50%|█████████████████████████████████████████████████                                                 | 16/32 [00:00<00:00, 1220.94it/s]16
Validation DataLoader 1:  53%|████████████████████████████████████████████████████                                              | 17/32 [00:00<00:00, 1223.27it/s]17
Validation DataLoader 1:  56%|███████████████████████████████████████████████████████▏                                          | 18/32 [00:00<00:00, 1224.85it/s]18
Validation DataLoader 1:  59%|██████████████████████████████████████████████████████████▏                                       | 19/32 [00:00<00:00, 1226.08it/s]19
Validation DataLoader 1:  62%|█████████████████████████████████████████████████████████████▎                                    | 20/32 [00:00<00:00, 1227.66it/s]20
Validation DataLoader 1:  66%|████████████████████████████████████████████████████████████████▎                                 | 21/32 [00:00<00:00, 1229.09it/s]21
Validation DataLoader 1:  69%|███████████████████████████████████████████████████████████████████▍                              | 22/32 [00:00<00:00, 1230.31it/s]22
Validation DataLoader 1:  72%|██████████████████████████████████████████████████████████████████████▍                           | 23/32 [00:00<00:00, 1231.45it/s]23
Validation DataLoader 1:  75%|█████████████████████████████████████████████████████████████████████████▌                        | 24/32 [00:00<00:00, 1232.12it/s]24
Validation DataLoader 1:  78%|████████████████████████████████████████████████████████████████████████████▌                     | 25/32 [00:00<00:00, 1233.07it/s]25
Validation DataLoader 1:  81%|███████████████████████████████████████████████████████████████████████████████▋                  | 26/32 [00:00<00:00, 1234.09it/s]26
Validation DataLoader 1:  84%|██████████████████████████████████████████████████████████████████████████████████▋               | 27/32 [00:00<00:00, 1234.86it/s]27
Validation DataLoader 1:  88%|█████████████████████████████████████████████████████████████████████████████████████▊            | 28/32 [00:00<00:00, 1235.67it/s]28
Validation DataLoader 1:  91%|████████████████████████████████████████████████████████████████████████████████████████▊         | 29/32 [00:00<00:00, 1236.08it/s]29
Validation DataLoader 1:  94%|███████████████████████████████████████████████████████████████████████████████████████████▉      | 30/32 [00:00<00:00, 1236.76it/s]30
Validation DataLoader 1:  97%|██████████████████████████████████████████████████████████████████████████████████████████████▉   | 31/32 [00:00<00:00, 1237.43it/s]31
Validation DataLoader 1: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████| 32/32 [00:00<00:00, 1237.89it/s]32
Validation DataLoader 1: |                                                                                                       | 33/? [00:00<00:00, 1238.71it/s]33
Validation DataLoader 1: |                                                                                                       | 34/? [00:00<00:00, 1239.63it/s]34
```


### Environment

<details>
  <summary>Current environment</summary>

```
#- PyTorch Lightning Version (e.g., 2.5.0):
#- PyTorch Version (e.g., 2.5):
#- Python version (e.g., 3.12):
#- OS (e.g., Linux):
#- CUDA/cuDNN version:
#- GPU models and configuration:
#- How you installed Lightning(`conda`, `pip`, source):
```

</details>


### More info

_No response_

cc [user]

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

[user] - I can take this issue .

### Comment 2 ([user]):

This issue has been automatically marked as stale because it hasn't had any recent activity. This issue will be closed in 7 days if no further activity occurs. Thank you for your contributions - the Lightning Team!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
