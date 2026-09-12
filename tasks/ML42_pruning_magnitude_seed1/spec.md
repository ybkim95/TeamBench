# ML42: Head Pruning by Weight Magnitude Instead of Gradient Importance

## Goal
Fix `prune.py` so `run()` uses **gradient-based attribution** for head importance,
not weight magnitude. Run `python prune.py` then `python check_pruning.py` — both must pass.

## Task
A **BERT-style encoder with structured head pruning** with 2 layers × 6 heads = 12 total heads.
6 heads (50%) are pruned. The bug: importance is measured by the L2 norm
of the Q/K/V weight matrices. This is a poor proxy — important heads can have small
weights, and unimportant heads may have large weights.

---

## The Bug: Weight Magnitude as Importance Proxy

### Background: Structured Head Pruning

After training, we want to remove (6) unimportant attention heads to reduce
inference cost. The key challenge: which heads are truly unimportant?

**Magnitude-based (buggy)**: `importance = L2_norm(Q_weights) + L2_norm(K_weights) + L2_norm(V_weights)`
- Fast to compute (no forward pass needed)
- Poor correlation with actual head utility
- Small-weight heads can still be critical (e.g., learned to suppress noise)

**Gradient-based attribution (correct)**:
```
importance = Σ_i |∂L/∂head_output_i × head_output_i|
```
- Measures how much the loss changes when this head varies
- Computed on calibration data via backward pass
- Proven to better preserve accuracy post-pruning (Michel et al., 2019)

### Current (Buggy) Code

```python
def run():
    importances_mag = compute_head_importance_magnitude(model)  # BUG: magnitude
    pruned_heads = prune_model(model, importances_mag, n_prune=6)
    results["pruning_method"] = "magnitude"   # BUG
```

### Correct Fix

```python
def run():
    # Use gradient attribution for importance — requires calibration data
    importances_grad = compute_head_importance_gradient(model, X_calib, y_calib, criterion)
    pruned_heads = prune_model(model, importances_grad, n_prune=6)
    results["pruning_method"] = "gradient_attribution"   # Correct
    results["pruning_ok"] = gradient_drop < magnitude_drop
```

The function `compute_head_importance_gradient()` is already implemented in `prune.py`
and uses gradient of Q projection weights as an importance proxy. Use it instead of
`compute_head_importance_magnitude()` for the primary pruning decision.

---

## Config
- embed_dim: 48, num_heads: 6, num_layers: 2
- n_train: 568, n_test: 345, n_calib: 197
- Prune ratio: 50% (6/12 heads), epochs: 19, lr: 0.001

## Deliverables
1. Fixed `prune.py` using `compute_head_importance_gradient()` for primary pruning
2. `pruning_results.json` with `pruning_method: "gradient_attribution"` and `pruning_ok: true`
3. `python check_pruning.py` exits 0
