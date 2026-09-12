# ML41: Drift Detector Monitors P(Y_hat) Instead of P(X)

## Goal
Fix `drift_detector.py` so `detect_drift()` monitors the **input feature distribution**
P(X), not the prediction distribution P(Y_hat). Run `python drift_detector.py` then
`python check_drift.py` — both must pass.

## Task
A **sensor reading classifier with distribution monitor** production monitoring system detects data drift by comparing
model predictions (P(Y_hat)) between reference and current data. However, this is
insensitive to covariate shift — the model may produce similar prediction distributions
on out-of-distribution inputs. A 1.5-sigma shift in all 20 features
goes undetected by prediction monitoring.

---

## The Bug: Monitoring Predictions Instead of Features

### Background: Types of Distribution Shift

**Covariate shift**: P(X) changes but P(Y|X) stays the same.
- Input features drift (sensor calibration, user behavior change)
- Model predictions may look similar despite degraded accuracy on new inputs

**Label shift**: P(Y) changes but P(X|Y) stays the same.
- Class proportions change
- P(Y_hat) monitoring detects this

**Current bug**: monitoring P(Y_hat) only detects label shift, not covariate shift.
For the 1.5-sigma covariate shift in this task, P(Y_hat) is similar
because the model assigns similar confidence to all classes on shifted inputs.

### Current (Buggy) Code

```python
def detect_drift(model, reference_x, current_x, threshold):
    # BUG: comparing prediction distributions P(Y_hat)
    ref_preds = model(reference_x).argmax(1).numpy().astype(float)
    curr_preds = model(current_x).argmax(1).numpy().astype(float)

    ks_stat, p_value = stats.ks_2samp(ref_preds, curr_preds)
    drift_detected = p_value < threshold
    results["monitor_type"] = "predictions"   # BUG
```

### Correct Fix

```python
def detect_drift(model, reference_x, current_x, threshold):
    # Correct: compare input feature distributions P(X)
    ref_np = reference_x.numpy()
    curr_np = current_x.numpy()

    feature_ks_stats = []
    feature_p_values = []
    for j in range(ref_np.shape[1]):
        s, p = stats.ks_2samp(ref_np[:, j], curr_np[:, j])
        feature_ks_stats.append(s)
        feature_p_values.append(p)

    # Drift if any feature shows significant shift
    ks_stat = max(feature_ks_stats)
    p_value = min(feature_p_values)
    drift_detected = p_value < threshold
    results["monitor_type"] = "features"   # Correct
```

---

## Config
- n_reference: 568, n_current: 445, n_train: 991
- Shift magnitude: 1.5σ, KS threshold: 0.1

## Deliverables
1. Fixed `drift_detector.py` with feature-based KS test
2. `drift_results.json` with `monitor_type: "features"` and `drift_detected: true`
3. `python check_drift.py` exits 0
