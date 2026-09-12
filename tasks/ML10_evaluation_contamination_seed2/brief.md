# ML10: Evaluation Contamination (Brief)

## Your Task
Fix `evaluate.py` for **cross-validation with test set leakage in pipeline** to eliminate test set contamination.

The current evaluation uses test set information during feature engineering,
producing optimistically inflated metrics.

## What You Know
- Evaluation code is in `evaluate.py`
- There are **3 contamination sources** (the Planner has each identified)
- After fixing, run `python evaluate.py` then `python check_evaluation.py`

## Rules
- Fix only `evaluate.py`
- Do not modify `check_evaluation.py`
- The test set must not be used in any fitting, encoding, or selection step
