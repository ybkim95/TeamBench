# DS10: Fairness Audit

## Task
Audit the **automated hiring screening model fairness audit** for disparate impact on protected groups.
Dataset: `data/predictions.csv` (2811 rows)

## Protected Attribute
`gender` — groups: `male`, `female`, `nonbinary`
Reference group: `male`

## Required Fairness Metrics
disparate_impact, demographic_parity_difference, equalized_odds

### 1. Disparate Impact (DI)
`DI = selection_rate(group) / selection_rate(reference_group)`
**Threshold**: DI < 0.8 = VIOLATION (EEOC 4/5 rule)

### 2. Demographic Parity Difference (DPD)
`DPD = selection_rate(group) - selection_rate(reference_group)`
Acceptable range: |DPD| < 0.10

### 3. Equalized Odds
Compare True Positive Rate and False Positive Rate across groups.
Both TPR and FPR should be similar across groups.

## Expected Results
- `male`: selection_rate=0.65, DI=1.000, OK
- `female`: selection_rate=0.47, DI=0.723, VIOLATION
- `nonbinary`: selection_rate=0.35, DI=0.538, VIOLATION

**Groups with violations**: `female`, `nonbinary`

## Requirements
1. Compute all three fairness metrics per group
2. Flag groups where DI < 0.8
3. Save to `fairness_report.json`:
   - Per-group: `disparate_impact`, `demographic_parity_difference`, `di_violation`
   - `violations_identified` must equal ['female', 'nonbinary']
   - `metrics_computed` must include all required metrics
4. Script: `audit.py`

## Deliverables
- Fixed `audit.py`
- `fairness_report.json` with all required metrics and correct violation flags
