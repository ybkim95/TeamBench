# ML7: Hyperparameter Search

## Goal
Fix `hyperparameter_search.py` so only valid hyperparameter combinations are tried.
`check_search.py` must report `invalid_combos_tried == 0`.

## Model: Svm With Invalid Kernel/Parameter Combinations
- Features: 10
- Samples: 546
- Classes: 2

---

## Invalid Parameter Combinations

### Bug 1: Kernel Degree

**Problem**: Degree parameter used with rbf/linear kernels (only valid for poly)

**Invalid range**: `non-poly kernels with degree param`

**Fix**: degree is only used when kernel='poly'. For kernel in ['rbf', 'linear', 'sigmoid'], the degree parameter is ignored but makes the search space misleading. Remove degree from non-poly configs.

### Bug 2: C

**Problem**: C <= 0 included in search space

**Invalid range**: `C <= 0`

**Fix**: SVM regularization parameter C must be > 0. Use np.logspace(-2, 3, 10) for C in [0.01, 1000].

### Bug 3: Gamma

**Problem**: Gamma='auto' deprecated, gamma=0 included

**Invalid range**: `gamma=0 or gamma=negative`

**Fix**: gamma must be 'scale', 'auto', or a positive float. gamma=0 raises ValueError. Use gamma='scale' as default.


---

## Valid Search Space (after fix)

```python
# Valid hyperparameter ranges for svm:
valid_lrs = list(np.logspace(-3, 0, 5))  # [0.001, ..., 1.0]




valid_C = [0.01, 0.1, 1.0, 10.0, 100.0]  # All > 0
valid_gamma = ['scale', 0.001, 0.01, 0.1]  # No zero/negative
```

## Deliverables
1. Fixed `hyperparameter_search.py` with valid search space only
2. `search_results.json` with `invalid_combos_tried == 0`
3. `check_search.py` exits 0
