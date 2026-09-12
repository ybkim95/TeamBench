# ML8: Distributed Training — Amp (Automatic Mixed Precision) Training Bugs

The distributed training code has gradient synchronization bugs.

## Task
Fix `distributed_train.py` so training converges correctly.

Run `python distributed_train.py` then `python check_training.py`.
