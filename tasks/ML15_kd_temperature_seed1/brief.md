# ML15: KD Temperature Asymmetry (Brief)

## Your Task
Fix the knowledge distillation loss in `train.py`.

Distilling from **large classifier teacher** to **compact classifier student**
with T=3.0 is producing a student that doesn't learn well.

## Symptoms
- Student accuracy much lower than teacher
- KD loss decreases but student doesn't match teacher's predictions

## What to Fix
- `train.py`: `kd_loss()` function — two related temperature bugs
- The Planner has the exact mathematical correction

## Success Criteria
- `python check_training.py` exits 0
- Student val accuracy > 0.65
