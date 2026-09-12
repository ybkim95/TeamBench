# ML31: Class Weights = Frequency Instead of Inverse Frequency

## Goal
Fix `weighting.py` so class weights are inversely proportional to class frequency.
Run `python train.py` then `python check_weighting.py` — both must pass.

## Task
Training a classifier on a **imbalanced multiclass classification with rare categories** (50% / 30% / 15% / 5%).
Class weights are used in `CrossEntropyLoss(weight=...)` to handle imbalance.

---

## The Bug: Frequency Weights Instead of Inverse Frequency

**Location**: `compute_class_weights()` in `weighting.py`

### Background: Weighted Cross-Entropy for Imbalanced Datasets

When classes are imbalanced, cross-entropy loss without weights makes the model
learn to predict the majority class. Class weighting compensates:

- **Majority class**: gets LOW weight → loss contribution reduced
- **Minority class**: gets HIGH weight → loss contribution amplified

### Current (Buggy) Code

```python
counts = np.bincount(y, minlength=n_classes).astype(np.float64)
weights = counts / (counts.sum() + 1e-8)  # BUG: high weight for common class
```

**Example** (4 classes, 50% / 30% / 15% / 5%):
| Class | Count | Buggy weight | Correct weight |
|-------|-------|--------------|----------------|
| 0 (majority) | ~700 | **0.700** | ~0.03 |
| 3 (minority) | ~50 | 0.050–0.100 | **~0.50** |

The bug amplifies the majority class signal, making the model even more biased.

### Correct Fix

```python
counts = np.bincount(y, minlength=n_classes).astype(np.float64)
weights = 1.0 / (counts + 1e-6)        # inverse frequency
weights = weights / weights.sum()       # normalize to sum=1
```

This gives rare classes high weights and common classes low weights.

### Effect on Training

| Metric | Buggy (freq) | Fixed (inv-freq) |
|--------|-------------|-----------------|
| Majority class acc | High | Moderate |
| Minority class recall | Near 0 | >0.30 |
| minority_upweighted | False | True |

---

## Training Config
- Classes: 4, Features: 20
- LR: 0.005, Epochs: 48, Batch: 32

## Deliverables
1. Fixed `weighting.py` with inverse-frequency class weights
2. `training_results.json` after running `python train.py`
3. `python check_weighting.py` exits 0
