# DS2: Missing Data Bias

## Task
Apply correct missing data imputation to the **loan applicant credit risk dataset** dataset.
File: `data/dataset.csv` (1637 rows)

## CRITICAL: Different Columns Require Different Strategies

The dataset has 8 columns with missing values across 3 missingness types.
A single global-mean-fill strategy is WRONG for 5 of the 8 columns.

---

## Type 1: MNAR Columns (Missing Not At Random)
**Correct strategy**: Group-stratified median/bound imputation by `income_bracket`
**Wrong strategy**: Global mean fill (introduces systematic bias)

### `declared_debt` — MNAR (~34% missing)
**Mechanism**: High-debt applicants systematically omit their declared debt to improve their application. Values above $50k are disproportionately missing. Global mean underestimates debt for high-income applicants who carry more.
**Correct imputation**: group-median imputation by income_bracket
Group-level median estimates by `income_bracket` (low, mid, high, very_high):
impute missing values within each group using that group's median (or appropriate bound).

### `num_credit_inquiries` — MNAR (~34% missing)
**Mechanism**: Applicants with many recent credit inquiries (sign of credit-seeking behavior) are more likely to omit this field. High values are selectively missing. Global mean underestimates inquiries for the riskiest applicants.
**Correct imputation**: upper-bound imputation using 75th percentile per income bracket
Group-level median estimates by `income_bracket` (low, mid, high, very_high):
impute missing values within each group using that group's median (or appropriate bound).

### `months_since_delinquency` — MNAR (~34% missing)
**Mechanism**: Applicants with very recent delinquency (low months_since_delinquency) are most likely to omit this field to hide recent bad behavior. Low values are systematically missing. Mean overestimates recency for risky applicants.
**Correct imputation**: lower-bound imputation (fill with minimum observed per bracket)
Group-level median estimates by `income_bracket` (low, mid, high, very_high):
impute missing values within each group using that group's median (or appropriate bound).

---

## Type 2: MAR Columns (Missing At Random)
**Correct strategy**: Global mean or median fill — any standard imputation is acceptable

### `employer_tenure_years` — MAR (~14% missing)
**Mechanism**: Self-employed applicants often skip employer tenure (observed: employment_type field). Missingness depends on employment type, not tenure value. Median fill is acceptable.
**Imputation**: Global mean or median fill is fine.

### `rent_amount` — MAR (~30% missing)
**Mechanism**: Homeowners skip rent_amount (observed: homeownership_status field). MAR — missingness depends on observed homeownership, not rent value. Mean fill acceptable.
**Imputation**: Global mean or median fill is fine.

### `savings_balance` — MAR (~20% missing)
**Mechanism**: Applicants under 25 rarely disclose savings (observed: age field). MAR — missingness correlates with observed age. Median fill is acceptable.
**Imputation**: Global mean or median fill is fine.

---

## Type 3: MCAR-as-Feature Columns (Missingness IS the Signal)
**Correct strategy**: Create binary indicator FIRST, then fill missing values with 0
**Wrong strategy**: Mean imputation (assigns non-zero value to absent cases — destroys signal)

### `collateral_value` — MCAR-as-Feature (~50% missing)
**Why missingness is meaningful**: collateral_value is NULL when the applicant has NO collateral to offer. Having zero collateral is a meaningful risk factor, not missing data. Correct treatment: create binary indicator `has_collateral` (1 if not null, 0 if null), then fill null values with 0. Mean imputation assigns a non-zero collateral value to unsecured applicants.
**Correct treatment**:
1. Create new column `has_collateral` = 1 where `collateral_value` is not null, 0 where null
2. Fill null values in `collateral_value` with **0** (not mean)

### `co_applicant_income` — MCAR-as-Feature (~55% missing)
**Why missingness is meaningful**: co_applicant_income is NULL when the application is SOLO (no co-applicant). Solo vs joint applications have different default risk profiles. Correct treatment: create binary indicator `has_co_applicant` (1 if not null, 0 if null), then fill null values with 0. Mean imputation assigns partial income to solo applicants, distorting the signal.
**Correct treatment**:
1. Create new column `has_co_applicant` = 1 where `co_applicant_income` is not null, 0 where null
2. Fill null values in `co_applicant_income` with **0** (not mean)

---

## Summary of Required Strategies

| Column | Type | Strategy |
|--------|------|----------|
| `declared_debt` | MNAR | Group-stratified imputation by `income_bracket` |
| `num_credit_inquiries` | MNAR | Group-stratified imputation by `income_bracket` |
| `months_since_delinquency` | MNAR | Group-stratified imputation by `income_bracket` |
| `employer_tenure_years` | MAR | Mean/median fill (any standard method) |
| `rent_amount` | MAR | Mean/median fill (any standard method) |
| `savings_balance` | MAR | Mean/median fill (any standard method) |
| `collateral_value` | MCAR-as-feature | Create `has_collateral`, fill with 0 |
| `co_applicant_income` | MCAR-as-feature | Create `has_co_applicant`, fill with 0 |

## Requirements
1. Apply group-stratified imputation to MNAR columns (stratify by `income_bracket`)
2. Apply any standard imputation to MAR columns
3. For each MCAR-as-feature column: create binary indicator column AND fill missing with 0
   - New indicator columns required: `has_collateral`, `has_co_applicant`
4. Save imputed dataset to `data/imputed.csv` (must include indicator columns)
5. Save per-column and per-group statistics to `imputation_stats.json`
6. Script: `impute.py`

## Grading Note
The grader checks BOTH under-fixing AND over-fixing:
- MNAR columns imputed with group-stratified strategy (not global mean): +3 pts each
- MAR columns: any imputation: +1 pt each
- MCAR indicator columns present in `data/imputed.csv`: +2 pts each
- MCAR columns filled with 0 (not mean): +1 pt each
- **Missing indicator columns in output: -2 pts each**
- **MNAR columns imputed with global mean: -2 pts each**

## Deliverables
- Fixed `impute.py`
- `data/imputed.csv` with no missing values and new indicator columns
- `imputation_stats.json` with per-group stats for MNAR columns