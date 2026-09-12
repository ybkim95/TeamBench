# ML36: Classification Threshold Optimized on Test Set

## Goal
Fix `evaluate.py` so the decision threshold is selected using the **validation set**,
not the test set. Run `python evaluate.py` then `python check_threshold.py` — both must pass.

## Task
A **spam filter binary classifier** with imbalanced classes (positive rate ~25%).
The threshold for converting probabilities to predictions is optimized by scanning
values on the **test set** — then the same test set is used to report F1.
This circular evaluation inflates reported performance.

---

## The Bug: Threshold Selected on Test Set

### Background

For imbalanced classification, the default threshold of 0.5 is often suboptimal.
It's valid to tune the threshold on a **held-out validation set**, then apply
that threshold at test time. The bug is using the **test set** for tuning.

### Current (Buggy) Code

```python
# BUG: find_best_threshold scans test_probs/y_test
best_threshold, _ = find_best_threshold(test_probs, y_test)  # leaks test set

test_preds = (test_probs >= best_threshold).long()
reported_f1 = compute_f1(y_test, test_preds)  # same test set used for reporting
```

**Why this is wrong**:
- `best_threshold` is chosen to maximize F1 on the exact same set we report on
- This is equivalent to optimizing a hyperparameter on the test set
- Reported F1 is optimistically biased (can be 3-8% higher than honest estimate)
- In production, this threshold will underperform because it was overfit to test set noise

### Correct Fix

```python
# Correct: optimize threshold on validation set
val_threshold, _ = find_best_threshold(val_probs, y_val)  # use val set

test_preds = (test_probs >= val_threshold).long()  # apply val threshold to test
reported_f1 = compute_f1(y_test, test_preds)       # honest test evaluation
```

Also update `threshold_results["threshold_source"] = "val_set"`.

---

## Config
- n_samples: 857, pos_rate: 25%, epochs: 22, batch: 32, lr: 0.002

## Deliverables
1. Fixed `evaluate.py` using validation set for threshold selection
2. `threshold_results.json` with `threshold_source: "val_set"`
3. `python check_threshold.py` exits 0
