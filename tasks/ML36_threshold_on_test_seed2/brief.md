# ML36: Threshold Optimized on Test Set (Brief)

## Your Task
Fix `evaluate.py` — the decision threshold is tuned on the test set (circular evaluation).

A **spam filter binary classifier** scans probability thresholds and picks the best one
based on test set F1, then reports that same test set's F1. This inflates performance.

## What to Fix
- `evaluate.py`: `find_best_threshold(test_probs, y_test)` → use `val_probs, y_val`
- Apply `val_threshold` to `test_probs` for final evaluation
- Set `threshold_source = "val_set"` in results

## Success Criteria
- `python check_threshold.py` exits 0
- `threshold_source == "val_set"`
- F1 inflation ≈ 0
