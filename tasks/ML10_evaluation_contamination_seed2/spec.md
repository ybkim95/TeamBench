# ML10: Evaluation Contamination

## Goal
Fix `evaluate.py` to eliminate all 3 evaluation contamination sources.
`check_evaluation.py` must pass.

## Problem Domain
**Cross-Validation With Test Set Leakage In Pipeline**
- Samples: 628
- Features: 16

---

## Why Evaluation Contamination Matters

Contaminated evaluation produces optimistically biased test metrics. The model
appears to generalize better than it does on truly unseen data. This leads to:
1. Deploying models that fail in production
2. Making wrong model selection decisions
3. Reporting inflated benchmark numbers in research

The golden rule: **the test set must be completely invisible during any fitting,
selection, or tuning step.**

---

## Contamination Sources

### Contamination Source 1: Preprocessing Outside Cv

**Problem**: Standardscaler applied before cross-validation (leaks fold statistics)

**Fix**: Wrap preprocessing in sklearn Pipeline inside cross_val_score. The scaler must be inside the CV loop.

**Result flag in `eval_results.json`**: `"preprocessing_outside_cv"` must be `false` after fix.

### Contamination Source 2: Test Set In Cv

**Problem**: Test set included in cross-validation folds

**Fix**: cross_val_score must only receive X_train, y_train — never X_test, y_test.

**Result flag in `eval_results.json`**: `"test_set_in_cv"` must be `false` after fix.

### Contamination Source 3: Feature Selection Outside Cv

**Problem**: Selectkbest fitted before cv, then features used inside cv

**Fix**: Include SelectKBest inside the Pipeline passed to cross_val_score.

**Result flag in `eval_results.json`**: `"feature_selection_outside_cv"` must be `false` after fix.


---

## Correct Evaluation Template

```python
# CORRECT order of operations:
X_train, X_test, y_train, y_test = train_test_split(X, y, ...)

# All fitting happens on X_train, y_train ONLY:
scaler.fit(X_train)
X_train_s = scaler.transform(X_train)
X_test_s = scaler.transform(X_test)   # transform only, never fit

pca.fit(X_train_s)
X_train_p = pca.transform(X_train_s)
X_test_p = pca.transform(X_test_s)

selector.fit(X_train_p, y_train)
X_train_f = selector.transform(X_train_p)
X_test_f = selector.transform(X_test_p)

# Hyperparameter tuning: use cross-validation on TRAINING set only
cv_scores = cross_val_score(model, X_train_f, y_train, cv=5)

# Final evaluation: test set used ONCE at the very end
model.fit(X_train_f, y_train)
test_acc = model.score(X_test_f, y_test)
```

## Required Changes to `eval_results.json`

After fix, these flags must all be `false`:
- `"preprocessing_outside_cv"`: false
- `"test_set_in_cv"`: false
- `"feature_selection_outside_cv"`: false

## Deliverables
1. Fixed `evaluate.py` with no contamination sources
2. `eval_results.json` with all contamination flags set to `false`
3. `check_evaluation.py` exits 0
