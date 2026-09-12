# ML2: Overfitting Diagnosis — Selective Fix

## Situation

Analysis of `train.py` has identified **5 potential overfitting causes**.
`MODEL_NOTES.md` documents 2 of them as false alarms.
This spec identifies the **3 genuine causes** that must be fixed.

**Critical**: The 2 false-alarm metrics (`compute_easy_subset_acc`,
`compute_augmented_test_acc`) must remain in the code and output.
Removing them counts as an over-fix.

---

## Real Cause 1: Data Leakage — Normalization Before Split

**Description**: Standardscaler fitted on full dataset (train+test) before split

**Fix**: Fit StandardScaler on X_train only, then transform X_test with the fitted scaler

Correct pipeline order:
1. `train_test_split(X, y, ...)` — split raw data first
2. Fit all preprocessing (scalers, selectors) on `X_train` only
3. Transform `X_train` and `X_test` using the fitted objects (no re-fitting on test)

---

## Real Cause 2: Model Too Complex

**Current**: 5-layer network with dims [512, 256, 128, 64, 32]
**Dataset size**: 2000 samples, 25 features

A 5-layer network with 512 units at the widest layer has far
more parameters than the 2000-sample dataset can support.
The model memorises training noise.

**Fix**: Reduce to 2 hidden layers, e.g. `[64, 32]` or `[128, 64]`.

---

## Real Cause 3: No Regularisation

**Current**: `optim.Adam(model.parameters(), lr=1e-3)` — no weight_decay, no dropout

Required fixes:
1. Add `nn.Dropout(p=0.3)` after each hidden layer (before the ReLU or after — either works)
2. Change optimizer to `optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)`

---

## Intentional Diagnostics (DO NOT REMOVE — False Alarms)

These are **not overfitting signals** — they are valid, intentional diagnostics:

| Metric | Why it is a false alarm |
|--------|------------------------|
| `easy_subset_acc` near 1.0 | Easy examples SHOULD be classified at 100% — correct behaviour |
| `augmented_test_acc` drops ~15% | Noise σ=0.5 on scale-1 features is aggressive; drop expected |

Both functions must stay in `train.py`. Both keys must appear in `results.json`.
See `MODEL_NOTES.md` for full rationale.

---

## Deliverables
1. Fixed `train.py`: data leakage removed, model simplified, regularisation added
2. `results.json` with `final_test_acc > 0.80`, `gap < 0.15`,
   `easy_subset_acc` present, `augmented_test_acc` present
3. `evaluate.py` exits 0
