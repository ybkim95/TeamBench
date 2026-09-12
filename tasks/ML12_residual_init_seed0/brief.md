# ML12: Residual Init Variance (Brief)

## Your Task
Fix the weight initialization bug in `model.py`.

Training a deep residual network (8 blocks) is not converging.
The issue is in how the residual blocks are initialized.

## Symptoms
- Loss decreases very slowly
- High variance in gradients at initialization
- `check_init_variance()` reports max variance >> 1

## What to Fix
- `model.py`: `ResBlock.__init__()` — how `fc2` is initialized
- The Planner has details on the correct initialization strategy
- Do NOT modify `train.py`

## Success Criteria
- `python check_training.py` exits 0
