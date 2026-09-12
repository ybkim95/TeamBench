# ML2: Overfitting Diagnosis (Brief)

## Your Task

Fix `train.py` for **hospital readmission prediction** so the model generalises.

Currently: ~99% training accuracy, ~52% test accuracy. This is severe overfitting.

## Important Warning

Analysis has flagged **5 potential overfitting causes**.
**Only 3 are genuine.** The other 2 are diagnostic metrics that must stay in the code.

Read `MODEL_NOTES.md` to understand the 2 false alarms before making any changes.
Removing those functions or their output keys will cause the check to fail.

## Instructions

- Wait for the Planner's diagnosis — they know which 3 causes are real
- Do NOT remove `compute_easy_subset_acc()` or `compute_augmented_test_acc()`
- Target: test accuracy >0.80, train-test gap <0.15

## Workflow

1. Read `MODEL_NOTES.md` (critical — explains what NOT to change)
2. Apply the Planner's 3 fixes to `train.py`
3. Run `python train.py` then `python evaluate.py`

## Rules
- Fix only `train.py`
- Do not modify `evaluate.py` or `MODEL_NOTES.md`
