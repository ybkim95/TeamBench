# ML47: Multi-Task Weighting Instability Bug (Brief)

## Your Task
Fix the multi-task loss weighting in `trainer.py`.

Training a **three-task mixed-difficulty learning** crashes with NaN losses because the
inverse-loss weighting scheme explodes when any task loss approaches zero.

## Symptoms
- Training crashes (NaN/Inf gradients) after a task becomes well-solved
- `training_results.json` shows `"crashed": true`
- Loss initially decreases then suddenly becomes NaN

## What to Fix
- `trainer.py`: `MultiTaskTrainer.weighted_loss()` — use `1/(loss.detach() + epsilon)`
- Two fixes needed: (1) add `.detach()`, (2) add `+ self.epsilon` to denominator
- Do NOT modify `train.py` or `model.py`

## Success Criteria
- `python check_multitask.py` exits 0
- Training converges without crashing (all val losses < 0.3)
