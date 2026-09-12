# ML40: Shadow Deployment Evaluation Mode Mismatch

## Goal
Fix `shadow_eval.py` so the shadow model is evaluated in `eval()` mode (same as production).
Run `python shadow_eval.py` then `python check_shadow.py` — both must pass.

## Task
A **text classifier shadow deployment** pipeline compares a production model against a shadow (candidate) model.
The production model runs in `eval()` mode (correct), but the shadow model is left in
`train()` mode with dropout active. This unfairly degrades shadow model predictions
(dropout_rate=0.3 causes significant noise), making the shadow model appear worse
than it actually is.

---

## The Bug: Shadow Model in train() Mode

### Background: Dropout in train() vs eval() Mode

**train() mode**: Dropout randomly zeroes `p=0.3` of activations at each forward pass.
- Output is stochastic and has higher variance
- Expected output is correct in expectation but individual predictions are noisy
- Confidence scores are artificially lowered

**eval() mode**: Dropout is disabled — all neurons active.
- Output is deterministic
- Full model capacity used for each prediction
- This is the correct mode for inference and evaluation

### Current (Buggy) Code

```python
prod_model.eval()       # Correct

shadow_model.train()    # BUG: dropout=0.3 active during evaluation
                        # Shadow predictions are noisy and biased downward

prod_metrics = compute_metrics(prod_model, X_shadow, y_shadow)
shadow_metrics = compute_metrics(shadow_model, X_shadow, y_shadow)  # unfair
```

**Effect**: Shadow model accuracy is artificially reduced by dropout noise. The comparison
concludes the shadow model is worse when it may actually be equally good or better.

### Correct Fix

```python
prod_model.eval()
shadow_model.eval()    # Match production eval mode — fair comparison

prod_metrics = compute_metrics(prod_model, X_shadow, y_shadow)
shadow_metrics = compute_metrics(shadow_model, X_shadow, y_shadow)  # fair
```

Also update `results["eval_mode_match"] = True` and `results["shadow_in_eval"] = True`.

---

## Config
- n_train: 668, n_test: 445, n_shadow: 395
- Dropout rate: 0.3, epochs: 19, lr: 0.001

## Deliverables
1. Fixed `shadow_eval.py` with `shadow_model.eval()` before evaluation
2. `shadow_results.json` with `eval_mode_match: true`, `shadow_in_eval: true`
3. `python check_shadow.py` exits 0
