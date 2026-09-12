# ML7: Hyperparameter Search

## Goal
Fix `hyperparameter_search.py` so only valid hyperparameter combinations are tried.
`check_search.py` must report `invalid_combos_tried == 0`.

## Model: Gradient Boosting With Invalid Hyperparameter Combinations
- Features: 12
- Samples: 791
- Classes: 2

---

## Invalid Parameter Combinations

### Bug 1: N Estimators

**Problem**: N_estimators=0 included in search space (invalid)

**Invalid range**: `[0, 0]`

**Fix**: n_estimators must be >= 1. Valid range: [10, 500]. Zero estimators raises ValueError.

### Bug 2: Learning Rate

**Problem**: Negative learning rates included in search space

**Invalid range**: `negative or zero values`

**Fix**: learning_rate must be in (0, 1]. Use np.logspace(-3, 0, 10) for range [0.001, 1.0].

### Bug 3: Subsample

**Problem**: Subsample >1.0 included (invalid probability)

**Invalid range**: `[1.01, 2.0]`

**Fix**: subsample must be in (0, 1.0]. Values >1.0 are invalid for GradientBoostingClassifier.


---

## Valid Search Space (after fix)

```python
# Valid hyperparameter ranges for gradient_boosting:
valid_lrs = list(np.logspace(-3, 0, 5))  # [0.001, ..., 1.0]


valid_n_estimators = [10, 50, 100, 200]  # All >= 1
valid_subsamples = [0.5, 0.6, 0.8, 1.0]  # All in (0, 1]


```

## Deliverables
1. Fixed `hyperparameter_search.py` with valid search space only
2. `search_results.json` with `invalid_combos_tried == 0`
3. `check_search.py` exits 0
