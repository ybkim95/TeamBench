# ML41: Drift Detector Wrong Signal (Brief)

## Your Task
Fix `drift_detector.py` — `detect_drift()` runs KS test on model predictions P(Y_hat)
instead of input features P(X). A 1.5-sigma covariate shift goes undetected.

The **sensor reading classifier with distribution monitor** monitoring pipeline should detect input feature drift,
not just label shift.

## What to Fix
- `drift_detector.py`: `detect_drift()` — replace prediction-based KS with per-feature KS
- Run `stats.ks_2samp` on each input feature, use `min(p_values)` for drift detection
- Set `monitor_type = "features"` in results

## Success Criteria
- `python check_drift.py` exits 0
- `monitor_type == "features"`
- `drift_detected == True` for 1.5-sigma shift
