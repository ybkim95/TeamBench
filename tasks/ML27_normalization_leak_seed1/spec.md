# ML27: Normalization Statistics Include Val/Test (Data Leakage)

## Goal
Fix `pipeline.py` so the normalizer is fit only on training data.
Run `python train.py` then `python check_pipeline.py` — both must pass.

## Task
Building a data pipeline for a **tabular regression dataset with mixed features** (regression).
The pipeline normalizes features before model training.

---

## The Bug: Scaler Fit Before Train/Val/Test Split

**Location**: `build_pipeline()` in `pipeline.py`

### Background

Feature normalization (zero-mean, unit-variance scaling) is essential for
gradient-based models. However, computing normalization statistics (mean, std)
from the full dataset — before splitting — causes **data leakage**:

- The scaler "sees" val/test examples during training
- Val/test distribution information leaks into the scaler parameters
- Model implicitly benefits from future data during training
- Validation metrics are optimistically biased

### Current (Buggy) Code

```python
# BUG: fit on ALL data — leaks val/test distribution
mean = X.mean(axis=0)        # uses all 30 features across all samples
std  = X.std(axis=0) + 1e-8  # uses all 30 features across all samples
X_scaled = (X - mean) / std  # scaled with contaminated stats

# Split AFTER scaling — too late, leak already happened
train_idx = idx[:n_train]
val_idx   = idx[n_train:n_train + n_val]
test_idx  = idx[n_train + n_val:]
```

### Correct Fix

```python
# Step 1: split indices FIRST
train_idx = idx[:n_train]
val_idx   = idx[n_train:n_train + n_val]
test_idx  = idx[n_train + n_val:]

# Step 2: fit scaler ONLY on training data
mean = X[train_idx].mean(axis=0)
std  = X[train_idx].std(axis=0) + 1e-8

# Step 3: apply to all splits using TRAIN stats
X_train_s = (X[train_idx] - mean) / std
X_val_s   = (X[val_idx]   - mean) / std  # transform with train stats
X_test_s  = (X[test_idx]  - mean) / std  # transform with train stats
```

Also update: `"fit_on_train_only": True`

### Why This Matters

| Approach | Uses val/test in scaler? | Leaks future info? |
|----------|--------------------------|--------------------|
| Full-data fit (bug) | Yes — all samples | Yes — distribution leak |
| Train-only fit (fix) | No — train only  | No — correct isolation |

The test distribution shift from large-scale features (`X[:, 0] *= 100`,
`X[:, 2] += 50`) makes the leak particularly significant.

---

## Training Config
- Features: 30, Task: regression
- LR: 0.005, Epochs: 48, Batch: 32
- Val fraction: 0.15, Test fraction: 0.15

## Deliverables
1. Fixed `pipeline.py` with split-before-fit and `fit_on_train_only=True`
2. `training_results.json` after running `python train.py`
3. `python check_pipeline.py` exits 0
