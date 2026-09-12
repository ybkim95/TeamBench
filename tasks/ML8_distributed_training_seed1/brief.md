# ML8: Distributed Training (Brief)

## Your Task
Fix `distributed_train.py` so training converges correctly.

The DistributedDataParallel gradient synchronization bugs code has bugs that prevent proper gradient flow:
loss doesn't decrease, or gradients are corrupted.

## What You Know
- Training code is in `distributed_train.py`
- There are **3 bugs** in the gradient handling logic
- The Planner has the correct ddp simulation protocol
- After fixing, run `python distributed_train.py` then `python check_training.py`

## Rules
- Fix only `distributed_train.py`
- Do not modify `check_training.py`
