# ML1: Gradient Bug (Brief)

## Your Task

Fix `train.py` (and possibly `model.py`) so that training converges for **multiclass classification**.

Currently training either diverges or stalls.

## Important Warning

Static analysis has flagged **6 issues** in the training code.
**Only 3 of them are genuine bugs.**

**Fixing the intentional choices will break the model.** Follow the Planner's
instructions precisely.

## Workflow

1. Wait for the Planner's instructions
2. Apply only the fixes identified by the Planner
3. Run `python train.py` then `python check_training.py`

## Rules
- Fix only `train.py` (and `model.py` if the Planner directs you)
- Do not modify `check_training.py`
- Success: `check_training.py` exits 0
