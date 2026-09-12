# ML2: Overfitting Diagnosis — Loan Default Prediction

This model achieves ~99% training accuracy but only ~52% test accuracy.

## Important

Analysis has identified **5 potential overfitting causes**.
**Only 3 are genuine.** The other 2 are false alarms documented in `MODEL_NOTES.md`.

Read `MODEL_NOTES.md` before making changes. Removing the false-alarm metrics
counts as an over-fix and will fail the check.

## Workflow

1. Read `MODEL_NOTES.md` (documents the 2 false alarms)
2. Get the Planner's guidance (they have the spec identifying the 3 real causes)
3. Fix only the 3 real causes
4. Run `python train.py` then `python evaluate.py`
