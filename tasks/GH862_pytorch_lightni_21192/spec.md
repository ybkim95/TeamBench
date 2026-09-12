# GH862_pytorch_lightni_21192: Fix lightning cli crashing when trainer defaults contain callback — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/Lightning-AI/pytorch-lightning/issues/21189
- Repo: https://github.com/Lightning-AI/pytorch-lightning

## Issue Description

### Bug description

```python
cli = LightningCLI(
    MyLightningModule,
    MyDataModule,
    trainer_defaults={
        "default_root_dir": log_dir,
        "logger": {
            "class_path": "lightning.pytorch.loggers.TensorBoardLogger",
            "init_args": {
                "save_dir": log_dir,
                "name": timestamp,
                "version": version,
            },
        },
        "callbacks": {
            "class_path": "lightning.pytorch.callbacks.ModelCheckpoint",
            "init_args": {
                "monitor": "val_loss",
                "mode": "min",
            }
        }
    },
    args=args,
    run=False,
    save_config_kwargs={"overwrite": True},
)
```
When specifying `callbacks` inside `trainer_defaults` of` LightningCLI`, I get the following error:

```
File ".../site-packages/lightning/pytorch/utilities/model_helpers.py", line 42, in is_overridden
    raise ValueError("Expected a parent")
ValueError: Expected a parent
```

### What version are you seeing the problem on?

v2.5

### Reproduced in studio

_No response_

### How to reproduce the bug

```python
from lightning.pytorch.cli import LightningCLI
from lightning.pytorch.demos.boring_classes import BoringModel, BoringDataModule

def main():
    cli = LightningCLI(
        BoringModel,
        BoringDataModule,
        trainer_defaults={
            "logger": {
                "class_path": "lightning.pytorch.loggers.TensorBoardLogger",
                "init_args": {
                    "save_dir": ".",
                    "name": "demo",
                },
            },
            "callbacks": {
                "class_path": "lightning.pytorch.callbacks.ModelCheckpoint",
                "init_args": {
                    "monitor": "val_loss",
                }
            },
        },
        run=False,
    )

if __name__ == "__main__":
    main()
```

### Error messages and logs

```
Traceback (most recent call last):
  File "demo.py", line 27, in <module>
    main()
  File "demo.py", line 5, in main
    cli = LightningCLI(
          ^^^^^^^^^^^^^
  File ".../site-packages/lightning/pytorch/cli.py", line 408, in __init__
    self.instantiate_classes()
  File ".../site-packages/lightning/pytorch/cli.py", line 584, in instantiate_classes
    self.trainer = self.instantiate_trainer()
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File ".../site-packages/lightning/pytorch/cli.py", line 598, in instantiate_trainer
    return self._instantiate_trainer(trainer_config, extra_callbacks)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File ".../site-packages/lightning/pytorch/cli.py", line 623, in _instantiate_trainer
    return self.trainer_class(**config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File ".../site-packages/lightning/pytorch/utilities/argparse.py", line 70, in insert_env_defaults
    return fn(self, **kwargs)
           ^^^^^^^^^^^^^^^^^^
  File ".../site-packages/lightning/pytorch/trainer/trainer.py", line 434, in __init__
    self._callback_connector.on_trainer_init(
  File ".../site-packages/lightning/pytorch/trainer/connectors/callback_connector.py", line 82, in on_trainer_init
    _validate_callbacks_list(self.trainer.callbacks)
  File ".../site-packages/lightning/pytorch/trainer/connectors/callback_connector.py", line 248, in _validate_callbacks_list
    stateful_callbacks = [cb for cb in callbacks if is_overridden("state_dict", instance=cb)]
                                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File ".../site-packages/lightning/pytorch/utilities/model_helpers.py", line 42, in is_overridden
    raise ValueError("Expected a parent")
ValueError: Expected a parent
```

### Environment

- Lightning version: 2.5.3
- Python version: 3.12
- OS: Ubuntu 22.04.5 LTS



### More info


### Behavior

I check the`is_overridden` function and try to print the instance

```python
def is_overridden(method_name: str, instance: Optional[object] = None, parent: Optional[type[object]] = None) -> bool:
    if instance is None:
        return False
    print(instance)
    print(type(instance))
    if parent is None:
        if isinstance(instance, pl.LightningModule):
            parent = pl.LightningModule
        elif isinstance(instance, pl.LightningDataModule):
            parent = pl.LightningDataModule
        elif isinstance(instance, pl.Callback):
            parent = pl.Callback
        if parent is None:
            _check_mixed_imports(instance)
            raise ValueError("Expected a parent")
```

and I got

```python
{'class_path': 'lightning.pytorch.callbacks.ModelCheckpoint', 'init_args': {...}}
<class 'dict'>
```

### Expected

Callbacks should be instantiated properly from the given class_path and init_args, just like logger.

This might not be a strict bug but an inconsistency: logger in trainer_defaults can be specified as a dict with class_path and init_args, while callbacks cannot. This leads to confusion because both are usually specified in config files the same way. It would be nice if callbacks supported the same dict syntax for consistency.

Note:  When specifying the callbacks in a config file, it works well and raises no error:

```
trainer:
  accelerator: auto
  strategy: auto
  devices: auto
  num_nodes: 1
  precision: null
  callbacks:
    class_path: lightning.pytorch.callbacks.ModelCheckpoint
    init_args:
      monitor: val_loss
      mode: min
      save_top_k: 1
      filename: "{epoch:02d}_{val_f1_epoch:.4f}_{val_auc_epoch:.4f}"
      save_weights_only: true
  fast_dev_run: false
  max_epochs: 20
```

cc [user]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
