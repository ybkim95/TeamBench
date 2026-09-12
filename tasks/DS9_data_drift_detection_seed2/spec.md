# DS9: Data Drift Detection

## Task
Monitor **customer churn model monitoring** for data drift.
Reference data: `data/reference.csv` (5231 rows from training period)
Production data: `data/production.csv` (2187 rows from deployment)

## CRITICAL: Feature Drift Status

### Drifted Features (MUST FLAG)
`engagement_score`, `support_tickets_30d`
- `engagement_score`: mean_shift (magnitude 40%)
- `support_tickets_30d`: distribution_shift (magnitude 35%)

### Stable Features (MUST NOT FLAG)
`tenure_months`, `monthly_spend`, `num_products`
Distribution unchanged from reference — flagging these is a false positive.

## Correct Drift Detection Methods

### PSI (Population Stability Index)
Threshold: PSI > 0.2 → drifted
- PSI 0–0.1: No drift
- PSI 0.1–0.2: Moderate drift (investigate)
- PSI > 0.2: Significant drift

### Kolmogorov-Smirnov Test
Threshold: p-value < 0.05 → drifted
Compares full distributions, not just means.

### Why Mean Difference Fails
Mean shifts catch only location drift. Variance increases and distribution shape changes
(bimodal, heavy-tail) are missed by simple mean comparison.

## Requirements
1. Apply PSI or KS test for each feature
2. Flag ONLY features with PSI > 0.2 or KS p < 0.05
3. Save to `drift_report.json`:
   - `drifted_features` must exactly equal ['engagement_score', 'support_tickets_30d']
   - `psi_computed` or `ks_test_applied` must be `true`
   - Per-feature metrics
4. Script: `monitor.py`

## Deliverables
- Fixed `monitor.py`
- `drift_report.json` with correct feature drift classification
