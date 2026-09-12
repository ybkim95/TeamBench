# ML35: Double Temperature Scaling Bug (Brief)

## Your Task
Fix the calibration pipeline in `model.py` and/or `evaluator.py`.

A **text classification model with post-hoc calibration** applies temperature `T=2.2` twice:
once in `model.forward()` and once in `evaluator.predict_proba()`.
This makes calibration worse (ECE stays high).

## What to Fix
- Remove temperature scaling from **one** of:
  - `model.py`: `CalibratedClassifier.forward()` — remove `/ self.temperature`
  - `evaluator.py`: `ModelEvaluator.predict_proba()` — remove `/ self.temperature`
- Do NOT remove temperature from both locations

## Success Criteria
- `python check_calibration.py` exits 0
- Test ECE < 0.10
