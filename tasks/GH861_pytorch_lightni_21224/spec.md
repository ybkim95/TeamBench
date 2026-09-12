# GH861_pytorch_lightni_21224: Bugfix for `BackboneFinetuning` + `LearningRateFinder` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/Lightning-AI/pytorch-lightning/issues/14674
- Repo: https://github.com/Lightning-AI/pytorch-lightning

## Issue Description

## 🐛 Bug

`auto_lr_find` does not properly restore the model for training if there is a `BackboneFinetuning` callback.

### To Reproduce

Specify a BackboneFinetuning callback, set auto_lr_find to True, and then run `tune` and `fit`.
```
trainer = Trainer(
    auto_lr_find=True,
    callbacks=[BackboneFinetuning()],
)
trainer.tune(model, train_dataloaders=train_data, val_dataloaders=val_data)
trainer.fit(model, train_dataloaders=train_data, val_dataloaders=val_data)
```
which will yield the following error

```
/usr/local/lib/python3.7/dist-packages/pytorch_lightning/callbacks/finetuning.py in on_fit_start(self, trainer, pl_module)
    103             for opt_idx, optimizer in enumerate(trainer.optimizers):
    104                 param_groups = self._apply_mapping_to_param_groups(
--> 105                     self._internal_optimizer_metadata[opt_idx], named_parameters
    106                 )
    107                 optimizer.param_groups = param_groups

KeyError: 0
```

See notebook example: https://colab.research.google.com/drive/1ajrSRge90RM8Rlcwk0HyEosLLpOpyvg-

### Expected behavior

It should be the case that after `auto_lr_find` runs, the model is reset and the found learning rate is used. 

### Environment

See bottom cell of colab notebook.

### Additional context

I think the culprit is that `on_fit_start` on `BackboneFinetuning` now calls the `on_fit_start` method of `BaseFinetuning`, which then thinks the model is being [restarted](https://github.com/eladsegal/pytorch-lightning/blob/5b09601888cc4fac09a0d4c69dc751759ac08fe3/pytorch_lightning/callbacks/finetuning.py#L104) from a checkpoint.

It looks like the bug got introduced in this PR: (withheld: the upstream fix is not part of the task)#diff-ac96be7ba54bac4d7dc79ee012a211498fb97689e37026fe8a1b06a359079224R410


The fix will need to both support the finetuning callbacks when training is resumed as well as as support using auto lr find when there is a backbone finetuning callback on the model.

cc [user] [user] [user]

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I came across the same issue 1.5 years later.

I cannot use both `BaseFinetuning` and `LearningRateFinder` at the same time, otherwise I get hit with `KeyError: 0`.

### Comment 2 ([user]):

Same for me
[user] [user] Any plans about it ?

### Comment 3 ([user]):

FYI still not working [user] [user]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
