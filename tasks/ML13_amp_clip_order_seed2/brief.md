# ML13: AMP Gradient Clip Order Bug (Brief)

## Your Task
Fix the AMP training loop in `train.py`.

Training a **deep tabular model with AMP** with gradient clipping and AMP is not
working correctly because of a PyTorch-specific ordering requirement.

## What to Fix
- `train.py`: The order of `scaler.unscale_()` and `clip_grad_norm_()` calls
- The Planner has the exact details on the correct order

## Success Criteria
- `python check_training.py` exits 0
- Validation accuracy > 0.65
