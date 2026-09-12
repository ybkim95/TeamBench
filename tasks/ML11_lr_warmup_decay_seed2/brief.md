# ML11: LR Warmup-Decay Bug (Brief)

## Your Task
Fix the learning rate scheduler in `scheduler.py`.

Training a **deep MLP for tabular data** is currently underperforming because the
LR warmup and cosine decay schedule is implemented incorrectly.

## Symptoms
- Training loss decreases slowly
- Validation accuracy plateaus below 0.65
- LR trace shows wrong shape (peak at warmup end is below base_lr)

## What to Fix
- `scheduler.py`: `WarmupCosineScheduler.get_lr()` method
- The warmup and cosine decay are composed in the wrong order
- Do NOT modify `train.py`

## Success Criteria
- `python check_training.py` exits 0
- Validation accuracy > 0.65
