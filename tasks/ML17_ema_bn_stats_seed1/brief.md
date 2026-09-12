# ML17: EMA BN Stats Bug (Brief)

## Your Task
Fix `ema.py` — the EMA update incorrectly applies decay to BatchNorm statistics.

Training a **deep BN network with EMA averaging** succeeds, but the EMA model used for inference
has poor accuracy because its BatchNorm statistics are wrong.

## Symptoms
- Training model achieves good accuracy
- EMA model accuracy is significantly lower
- Gap between train_acc and ema_acc in training_results.json

## What to Fix
- `ema.py`: `ModelEMA.update()` — different handling for BN running stats
- The Planner has the exact fix

## Success Criteria
- `python check_training.py` exits 0
- EMA model accuracy > 0.65
