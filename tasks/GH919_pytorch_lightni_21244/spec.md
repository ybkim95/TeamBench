# GH919_pytorch_lightni_21244: Fix `last.ckpt` only being saved when another checkpoint has been created — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/Lightning-AI/pytorch-lightning/issues/20245
- Repo: https://github.com/Lightning-AI/pytorch-lightning

## Issue Description

### Bug description

According to the discussion in #4335 the intended functionality of `save_last` is the deterministic access to the last stored checkpoint in order to resume training. The [documentation](https://github.com/Lightning-AI/pytorch-lightning/blob/master/src/lightning/pytorch/callbacks/model_checkpoint.py#L87C9-L89C58) states similarly: 

> save_last: When ``True``, saves a `last.ckpt` copy whenever a checkpoint file gets saved. Can be set to ``'link'`` on a local filesystem to create a symbolic link. This allows accessing the latest checkpoint a deterministic manner. Default: ``None``.

But unfortunately `_save_last_checkpoint` may be called without any previous checkpoint existing. Some example configuration:
```python
ModelCheckpoint(
    filename='temp_backup',
    save_last=True,
    train_time_interval=datetime.timedelta(minutes=30), 
)
```
This will create a `last.ckpt` at the end of very epoch (either train or validation depending on `save_on_train_epoch_end`) - though no other checkpointing has triggered before. This is due to the `_save_last_checkpoint` called either way [at the epoch end](https://github.com/Lightning-AI/pytorch-lightning/blob/master/src/lightning/pytorch/callbacks/model_checkpoint.py#L326):

```python
def on_train_epoch_end(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule") -> None:
    """Save a checkpoint at the end of the training epoch."""
    if not self._should_skip_saving_checkpoint(trainer) and self._should_save_on_train_epoch_end(trainer): 
        monitor_candidates = self._monitor_candidates(trainer)
        if self._every_n_epochs >= 1 and (trainer.current_epoch + 1) % self._every_n_epochs == 0:
            self._save_topk_checkpoint(trainer, monitor_candidates)
        self._save_last_checkpoint(trainer, monitor_candidates)  # < --- here
```
Hence in the end (ironically) `save_last` does what it was not intended to do: save the last epoch. In case of `save_last='link'` this is resolved after the first triggering - afterwards the regular `_save_last_checkpoint` calls will only write identical soft links to the actual checkpoint file. There are more possible configurations for this to happen:
```python
ModelCheckpoint(
    monitor='val_loss',
    save_last=True,
    every_n_train_steps=1000
)
```
Even if [after 2000 steps](https://github.com/Lightning-AI/pytorch-lightning/blob/master/src/lightning/pytorch/callbacks/model_checkpoint.py#L316) `_save_topk_checkpoint` omits the creation of a new file (via `_save_monitor_checkpoint` detecting [no improvement](https://github.com/Lightning-AI/pytorch-lightning/blob/master/src/lightning/pytorch/callbacks/model_checkpoint.py#L700C9-L700C33)) `_save_last_checkpoint` is [triggered](https://github.com/Lightning-AI/pytorch-lightning/blob/master/src/lightning/pytorch/callbacks/model_checkpoint.py#L317). 

These additional (unintended) creations of checkpoints may cause severe delays between epochs. I am also pretty sure this is the  cause of numerous issues. A quick search revealed e.g. #20075, #19845, #17916.

Another problem is actually breaking the interplay of using multiple ModelCheckpoints - creating the chance that `last.ckpt` is actually **not** the latest checkpoint. 
```python
cpt_a = ModelCheckpoint(
    monitor='val_loss',
    file_name='epoch{epoch:02d}-val_loss{val_loss:.2f}',
    save_last='link',
    save_on_train_epoch_end=False,
    enable_version_counter=False,
)
cpt_b = ModelCheckpoint(
    filename="temp_backup",
    save_last="link",
    train_time_interval=datetime.timedelta(minutes=30),
    enable_version_counter=False,
)
```
The intended behavior would be to have (after some while) one checkpoint file according to the best loss value, one `temp_backup.ckpt` file and a softlink `last.ckpt` pinpointing to whatever of the above was stored later (in case training gets interrupted and needs to be resumed). But the following may happen:
 - some epoch finishes and cpt_a detects a new best loss value and stores the full file, `last.ckpt` points to that file
 - cpt_b gets triggered and stores the `temp_backup.ckpt`, `last.ckpt` is updated to point towards `temp_backup.ckpt`
 - from now on the `last.ckpt` pointer is only determined by the order of checkpoint execution. For both cpt_a and cpt_b whenever another epoch finishes the call to `_save_last_checkpoint` will make `last.ckpt` point to their checkpoint - teven if cpt_a detects a new best validation loss and cpt_b is triggered after cpt_a `last.ckpt` will for the majority of time point to `temp_backup.ckpt`

Also note this example where `last.ckpt` will be a corrupted symlink:
```python
ModelCheckpoint(
    filename="temp_backup",
    save_last="link",
    train_time_interval=datetime.timedelta(minutes=30),
)
```
During the first "end of epoch call" of `_save_last_checkpoint` it is [detected](https://github.com/Lightning-AI/pytorch-lightning/blob/master/src/lightning/pytorch/callbacks/model_checkpoint.py#L693) that no previous checkpoint was stored (`self._last_checkpoint_saved` is initialized as empty string):
```python
if self.save_last == "link" and self._last_checkpoint_saved and self.save_top_k != 0:
    self._link_checkpoint(trainer, self._last_checkpoint_saved, filepath)
else:
    self._save_checkpoint(trainer, filepath)
```
but in the next iteration (next epoch) the first case is satisfied and ModelCheckpoint will symlink `last.ckpt` to itself...

As a clean solution I would assume that no need for a "top-level"  `_save_last_checkpoint` should be required - based on a downstream [trigger](https://github.com/Lightning-AI/pytorch-lightning/blob/master/src/lightning/pytorch/callbacks/model_checkpoint.py#L389) of `_save_checkpoint` the logic to update/generate the `last.ckpt` should live. As an ad-hoc solution I tested the following
```python
class MyModelCheckpoint(ModelCheckpoint):
    def _save_last_checkpoint(self, trainer: "lightning.Trainer", monitor_candidates: Dict[str, torch.Tensor]) -> None:
        """Only update last checkpoint in case there has just been a new checkpoint."""
        if self._last_global_step_saved == trainer.global_step:
            super()._save_last_checkpoint(trainer=trainer, monitor_candidates=monitor_candidates)
```
which resolved all problems mentioned above. As additional speed improvement the `_save_last_checkpoint` calls at the end of each epoch could also be slightly re-arranged
```python
def on_train_epoch_end(self, trainer: "lightning.Trainer", pl_module: "lightning.LightningModule") -> None:
    """Save a checkpoint at the end of the training epoch."""
    if not self._should_skip_saving_checkpoint(trainer) and self._should_save_on_train_epoch_end(trainer):
        monitor_candidates = self._monitor_candidates(trainer)
        if self._every_n_epochs >= 1 and (trainer.current_epoch + 1) % self._every_n_epochs == 0:
            self._save_topk_checkpoint(trainer, monitor_candidates)
            self._save_last_checkpoint(trainer, monitor_candidates)
```

### What version are you seeing the problem on?

v2.3

### How to reproduce the bug

_No response_

### Error messages and logs

```
# Error messages and logs here please
```


### Environment

<details>
  <summary>Current environment</summary>

```
#- PyTorch Lightning Version 2.3.3
#- PyTorch Version 2.4.0
#- Python version 3.8.13
#- OS Linux
#- CUDA version 12.2
#- GPU models and configuration: Nvidia GeForce RTX 3090
#- How you installed Lightning: via pip inside a conda env
```

</details>


### More info

_No response_

cc [user] [user]

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I noticed an issue today that is (I think) a manifestation of this bug. 

I was training a model with:
* `save_top_k=5`
* `save_last=True`
* `mode='max'`

However, I was monitoring a "lower is better" signal mistake, so the 5 checkpoints that were saved were from the **first** 5 epochs (where error was highest). After loading up `last.ckpt`, the validation performance was identical to the **final state** of the model as reported on Tensorboard (and did not match the performance of any of the other saved checkpoints). 

We can see that `last.ckpt` was saved well after the others: 
```
drwxr-xr-x 1 ecole domain users   0 Aug 27 23:31  .
drwxr-xr-x 1 ecole domain users   0 Aug 27 23:29  ..
-rw------- 1 ecole domain users 83M Aug 27 23:29 'epoch=0-step=30.ckpt'
-rw------- 1 ecole domain users 83M Aug 27 23:30 'epoch=1-step=60.ckpt'
-rw------- 1 ecole domain users 83M Aug 27 23:30 'epoch=2-step=90.ckpt'
-rw------- 1 ecole domain users 83M Aug 27 23:30 'epoch=3-step=120.ckpt'
-rw------- 1 ecole domain users 83M Aug 27 23:31 'epoch=4-step=150.ckpt'
-rw------- 1 ecole domain users 83M Aug 27 23:37  last.ckpt
```

I was confused by this behavior, but it seems like this bug could explain it.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
