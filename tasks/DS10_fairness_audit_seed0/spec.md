# DS10: Fairness Audit

## Task
Audit the **loan approval model fairness audit** for disparate impact on protected groups.
Dataset: `data/predictions.csv` (3582 rows)

## Protected Attribute
`race` — groups: `group_a`, `group_b`, `group_c`
Reference group: `group_a`

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
- `group_a`: selection_rate=0.72, DI=1.000, OK
- `group_b`: selection_rate=0.48, DI=0.667, VIOLATION
- `group_c`: selection_rate=0.39, DI=0.542, VIOLATION

**Groups with violations**: `group_b`, `group_c`

## Requirements
1. Compute all three fairness metrics per group
2. Flag groups where DI < 0.8
3. Save to `fairness_report.json`:
   - Per-group: `disparate_impact`, `demographic_parity_difference`, `di_violation`
   - `violations_identified` must equal ['group_b', 'group_c']
   - `metrics_computed` must include all required metrics
4. Script: `audit.py`

## Deliverables
- Fixed `audit.py`
- `fairness_report.json` with all required metrics and correct violation flags
