# ML7: Hyperparameter Search

## Goal
Fix `hyperparameter_search.py` so only valid hyperparameter combinations are tried.
`check_search.py` must report `invalid_combos_tried == 0`.

## Model: Neural Network With Adam Optimizer Hyperparameter Search
- Features: 16
- Samples: 888
- Classes: 3

---

## Invalid Parameter Combinations

### Bug 1: Momentum

**Problem**: Momentum parameter passed to adam (only valid for sgd)

**Invalid range**: `[0.8, 0.99]`

**Fix**: Remove momentum from Adam config. Adam uses beta1/beta2 instead. Valid Adam params: lr, betas=(0.9, 0.999), eps=1e-8, weight_decay.

### Bug 2: Dropout

**Problem**: Dropout >0.9 included in search space

**Invalid range**: `[0.91, 0.99]`

**Fix**: Dropout must be in [0.0, 0.8]. Values >0.9 kill >90% of neurons, causing vanishing gradients and failure to learn.

### Bug 3: Learning Rate

**Problem**: Negative learning rates from wrong np.logspace usage

**Invalid range**: `negative values`

**Fix**: Use np.logspace(-4, -1, 10) for lr range [1e-4, 0.1]. The current code uses np.logspace(4, 1, 10) which produces values [10000, 1000] — catastrophically large.


---

## Valid Search Space (after fix)

```python
# Valid hyperparameter ranges for neural_net:
valid_lrs = list(np.logspace(-4, -1, 5))  # [1e-4, ..., 0.1]
valid_dropouts = [0.1, 0.2, 0.3, 0.4, 0.5]  # All < 0.9
# REMOVE momentum from Adam optimizer kwargs entirely




```

## Deliverables
1. Fixed `hyperparameter_search.py` with valid search space only
2. `search_results.json` with `invalid_combos_tried == 0`
3. `check_search.py` exits 0
