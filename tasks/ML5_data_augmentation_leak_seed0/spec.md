# ML5: Data Augmentation Leak — Selective Fix

## Situation

`augment_pipeline.py` has **5 flagged pipeline steps**.
`PIPELINE_DESIGN.md` documents 3 as #  choices.
This spec identifies the **2 genuine bugs** that must be fixed.

**Critical**: Label smoothing, AUGMENTATION_SEED=42, and `tta_predict()` must
not be removed. The check validates all three preservation flags.

---

## Real Bug 1: Augmentation Applied Before Split

**Current (buggy) order**:
```
augment_data(X, y)          ← WRONG: operates on full dataset
train_test_split(X_aug, y_aug)  ← test set now contains near-duplicates of training
```

**Correct order**:
```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y
)
X_train_aug, y_train_aug = augment_data(X_train, y_train)  # train only
```

**Why it matters**: With `AUG_FACTOR=3`, each original sample
gets 2 near-duplicate copies. Augmenting before splitting
places these near-duplicates in both train and test sets, inflating test accuracy.
After the fix, `n_test ≈ 125` (original only) and `n_train ≈ 1125` (augmented).

---

## Real Bug 2: StandardScaler Fitted Before Split

**Current (buggy)**:
```python
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_aug)  # fitted on train+test combined
X_train, X_test, ... = train_test_split(X_scaled, ...)
```

**Correct**:
```python
X_train, X_test, ... = train_test_split(X, ...)
X_train_aug, y_train_aug = augment_data(X_train, y_train)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_aug)   # fit on train only
X_test_scaled  = scaler.transform(X_test)             # transform only, no fit
```

**Why it matters**: Fitting the scaler on the full dataset (including test) leaks
the test distribution's mean and variance into the training normalisation.
The `normalization_applied_before_split` flag must be set to `False`.

---

## Intentional Choices (DO NOT REMOVE)

| Choice | Code | Why Intentional |
|--------|------|-----------------|
| Label smoothing | `apply_label_smoothing(ε=0.1)` | Regularisation for noisy labels |
| Fixed aug seed | `AUGMENTATION_SEED = 42` | Reproducibility requirement |
| TTA evaluation | `tta_predict(model, X_test, scaler)` | Correct evaluation protocol |

Removing any of these causes the check to fail.
See `PIPELINE_DESIGN.md` for full rationale.

---

## Required State of `pipeline_results.json` After Fix

```json
{
  "augmentation_applied_before_split":  false,
  "normalization_applied_before_split": false,
  "label_smoothing_preserved":          true,
  "augmentation_seed_preserved":        true,
  "tta_preserved":                      true,
  "n_test":  ~125,
  "n_train": ~1125
}
```

## Deliverables
1. Fixed `augment_pipeline.py` with correct split-first-then-augment order,
   scaler fitted on train only, intentional choices preserved
2. `pipeline_results.json` matching the above
3. `check_pipeline.py` exits 0


# Pipeline Design Document

This document explains deliberate design choices in `augment_pipeline.py` that
analysis may flag as data leakage or bad practice.

**Read this before modifying any pipeline code.**

---

## §Label Smoothing — `apply_label_smoothing(ε=0.1)`

**What analysis flags**: Label smoothing is applied in the pipeline, which analysis
tools may flag as "modifying labels — possible data manipulation".

**Why it is correct**: Label smoothing (ε=0.1) is a regularisation technique applied to the one-hot targets. It is applied after the train/test split using the training labels only; applying it to test labels during inference is harmless because TTA aggregation uses the raw predicted probabilities, not smoothed targets. Label smoothing reduces overconfident predictions and is the standard recipe for this plant disease model. Removing it increases val loss by ~5%.

`apply_label_smoothing()` must remain in `augment_pipeline.py`.
The `label_smoothing_preserved` flag in `pipeline_results.json` must be `True`.

---

## §Shared Augmentation Seed — `AUGMENTATION_SEED = 42`

**What analysis flags**: A fixed global random seed for augmentation looks like
it could cause correlated augmentation patterns across train and test.

**Why it is correct**: The shared random seed (AUGMENTATION_SEED=42) across all augmentation operations is intentional for reproducibility. With a fixed seed, each run produces identical augmented batches, enabling fair comparison across experiments and debugging. Using per-call random seeds makes results non-reproducible between runs.

`AUGMENTATION_SEED = 42` must remain unchanged.
The `augmentation_seed` field in `pipeline_results.json` must equal `42`.

---

## §Test-Time Augmentation — `tta_predict()`

**What analysis flags**: Applying training-time augmentation operations to the
test set looks like "data leakage from training distribution into test".

**Why it is correct**: Test-Time Augmentation (TTA) applies the SAME geometric transforms as training-time augmentation and averages predictions. This is the correct and standard evaluation protocol for geometric augmentations — the model was trained to be robust to these transforms, so averaging predictions under them reduces variance and improves accuracy by ~1-2%. Using different transforms at test time than train time would be incorrect.

`tta_predict()` must remain in `augment_pipeline.py` and be used for test evaluation.
The `tta_preserved` flag in `pipeline_results.json` must be `True`.

---

## Known Real Bugs (NOT documented here)

There are 2 genuine pipeline ordering bugs in `augment_pipeline.py`.
Consult the spec for details. The sections above cover only the **intentional
choices** that must be preserved.
