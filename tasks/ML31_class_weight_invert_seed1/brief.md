# ML31: Class Weight Inversion Bug (Brief)

## Your Task
Fix the class weighting in `weighting.py`.

A **imbalanced multiclass classification with rare categories** uses class weights proportional to frequency
(`counts / counts.sum()`). This amplifies majority-class bias instead of
compensating for imbalance. Minority class recall is near zero.

## What to Fix
- `weighting.py`: `compute_class_weights()` — use `1.0 / counts` (inverse frequency)
- Normalize so weights sum to 1
- The minority class (class 3) must have higher weight than majority (class 0)
- Do NOT modify `train.py`

## Success Criteria
- `python check_weighting.py` exits 0
- Minority class recall > 0.30
- `minority_upweighted=True` in training_results.json
