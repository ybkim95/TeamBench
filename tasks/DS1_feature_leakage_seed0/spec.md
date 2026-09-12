# DS1: Feature Leakage Detection

## Task
Build a binary classifier for **loan applicant credit default prediction** (target: `defaulted`).
Dataset: `data/dataset.csv`

## Context
The dataset contains 7 columns that could be considered suspicious due to correlation with
the target. However, only 4 of them are genuine leakage. The other 3 are **intentionally
included valid predictors** — removing them will REDUCE model performance.

A naive "remove all correlated features" approach will score WORSE than the selective fix.

## Feature Classification

### Group A — LEAKY: Temporal Leakage (MUST EXCLUDE)
Columns: `payment_status_after_1month`, `days_past_due_final`
**Why they leak**: recorded after the default event occurred — pure target leakage
These are only populated for positive-class examples — a dead giveaway.

### Group B — LEAKY: Proxy Leakage (MUST EXCLUDE)
Column: `internal_risk_score`
**Why it leaks**: computed directly from the target variable by the data warehouse after loan resolution
Will show near-perfect correlation with `defaulted` in EDA.

### Group C — LEAKY: Direct Leakage (MUST EXCLUDE)
Column: `loan_outcome_code`
**Why it leaks**: direct encoding of the target with minor label transformation
Values are essentially identical to `defaulted`.

---

### Group D — VALID CORRELATED FEATURES (MUST KEEP)
Columns: `debt_ratio`, `credit_score_prev`, `num_late_payments_prev`
**Why they are valid (NOT leakage)**: debt_ratio, credit_score_prev, and num_late_payments_prev are pre-application financial indicators recorded BEFORE the loan decision. They correlate with default because they reflect creditworthiness, which is exactly what we want to predict. These are legitimate predictive features, not leakage.

These correlate with the target because they are genuine risk indicators measured
**before** the outcome. Removing them is an overcorrection that destroys model signal.

---

### Uncorrelated Features (use as-is)
`income`, `employment_years`, `num_credit_lines`, `monthly_expenses`, `zip_region_code`

## Correct Feature Set
Use ONLY: the uncorrelated features + Group D (valid correlated).
Exclude: Groups A, B, C.

## Requirements
1. Exclude all leaky columns (Groups A, B, C)
2. **Keep** the valid correlated columns (Group D) — do NOT remove them
3. Train classifier on the correct feature set
4. Evaluate on held-out test set (20% split, random_state=42)
5. Achieve ROC-AUC ≥ 0.75 on the correct feature set
6. Save to `results.json` with keys: `auc`, `features_used`, `n_features`
7. Script: `train.py`

## Grading Note
The grader checks BOTH directions:
- Penalizes if leaky columns appear in `features_used`
- **Also penalizes if valid correlated columns are ABSENT from `features_used`**
Removing Group D (over-fixing) scores lower than only removing Groups A/B/C.

## Deliverables
- Fixed `train.py`
- `results.json` with AUC and feature list
