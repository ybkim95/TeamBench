# ML28: Multi-Label Stratification by Single Label

## Goal
Fix `splitter.py` so the train/val split stratifies by ALL labels, not just the first.
Run `python train.py` then `python check_splitter.py` — both must pass.

## Task
Building a stratified train/val split for a **multi-label text tagging dataset**.
The dataset has 4 labels: ['topic_A', 'topic_B', 'urgent', 'long_form'].
Labels are correlated (e.g., labels 0 & 1 co-occur frequently; label 3 is rare ~10%).

---

## The Bug: Single-Label Stratification Ignores Co-Occurrence

**Location**: `stratified_split()` in `splitter.py`

### Background: Multi-Label Stratification

When splitting a multi-label dataset, stratifying by a single label produces
splits where the joint distribution of label combinations can be very different:

- Example: if `(label_0=1, label_3=1)` co-occurs in 5% of samples, a single-label
  split may put all of these in train or all in val by chance.
- The rare label (label_3, ~10% positive) is particularly sensitive.

### Current (Buggy) Code

```python
# BUG: only the first label is used for stratification
stratify_key = y[:, 0]  # ignores labels 1..3
```

**Problems**:
1. Rare label combinations may be entirely in one split
2. Correlated label pairs (0 & 1) won't have matched co-occurrence rates
3. Validation metrics are biased due to distribution mismatch

### Correct Fix

Use a composite key capturing all 4 labels:

```python
# Option A: string concatenation
label_keys = np.array([''.join(map(str, row)) for row in y])

# Option B: structured key
label_keys = np.array([tuple(row.tolist()) for row in y], dtype=object)

# Then stratify by composite key
stratify_key = label_keys
```

Also update: `"stratify_all_labels": True`

### Distribution Comparison

| Split | label_0 rate | label_3 rate (rare) | co-occurrence (0&1) |
|-------|-------------|-------------------------------|----------------------|
| Buggy train | ~50% | varies widely | uncontrolled |
| Buggy val   | ~50% | varies widely | uncontrolled |
| Fixed train | ~50% | ~10%          | controlled   |
| Fixed val   | ~50% | ~10%          | controlled   |

---

## Training Config
- Labels: 4 (['topic_A', 'topic_B', 'urgent', 'long_form'])
- LR: 0.002, Epochs: 33, Batch: 32, Val fraction: 0.2

## Deliverables
1. Fixed `splitter.py` with composite-key stratification
2. `training_results.json` after running `python train.py`
3. `python check_splitter.py` exits 0
