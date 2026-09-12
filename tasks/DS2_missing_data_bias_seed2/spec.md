# DS2: Missing Data Bias

## Task
Apply correct missing data imputation to the **employee wellness and attrition risk dataset** dataset.
File: `data/dataset.csv` (1557 rows)

## CRITICAL: Different Columns Require Different Strategies

The dataset has 8 columns with missing values across 3 missingness types.
A single global-mean-fill strategy is WRONG for 5 of the 8 columns.

---

## Type 1: MNAR Columns (Missing Not At Random)
**Correct strategy**: Group-stratified median/bound imputation by `seniority_band`
**Wrong strategy**: Global mean fill (introduces systematic bias)

### `stress_self_report` — MNAR (~26% missing)
**Mechanism**: Highly stressed employees are less likely to complete wellness surveys. High stress scores (>7) are systematically missing. Global mean imputation underestimates stress levels for the most at-risk employees.
**Correct imputation**: group-median imputation by seniority_band
Group-level median estimates by `seniority_band` (junior, mid, senior, executive):
impute missing values within each group using that group's median (or appropriate bound).

### `manager_rating` — MNAR (~26% missing)
**Mechanism**: Poor-performing employees are less likely to submit manager ratings because low ratings feel uncomfortable to provide. Values below 3 are selectively missing. Mean imputation overestimates manager ratings for the at-risk population.
**Correct imputation**: lower-bound imputation (25th percentile per seniority_band)
Group-level median estimates by `seniority_band` (junior, mid, senior, executive):
impute missing values within each group using that group's median (or appropriate bound).

### `overtime_hours_monthly` — MNAR (~26% missing)
**Mechanism**: Employees working excessive overtime (>60h/month) often do not report it accurately due to policy concerns. High overtime hours are systematically underreported (missing). Mean underestimates overtime for the most burned-out employees who are highest attrition risk.
**Correct imputation**: group-median imputation by seniority_band
Group-level median estimates by `seniority_band` (junior, mid, senior, executive):
impute missing values within each group using that group's median (or appropriate bound).

---

## Type 2: MAR Columns (Missing At Random)
**Correct strategy**: Global mean or median fill — any standard imputation is acceptable

### `commute_time_minutes` — MAR (~25% missing)
**Mechanism**: Remote workers skip commute time (observed: work_arrangement field). MAR — depends on observed work arrangement. Median fill is acceptable.
**Imputation**: Global mean or median fill is fine.

### `last_salary_increase_pct` — MAR (~16% missing)
**Mechanism**: New hires (<6 months) have no salary increase on record (observed: tenure field). MAR — depends on observed tenure. Mean fill acceptable.
**Imputation**: Global mean or median fill is fine.

### `training_hours_ytd` — MAR (~13% missing)
**Mechanism**: Part-time employees rarely participate in training programs (observed: employment_type). MAR. Median fill acceptable.
**Imputation**: Global mean or median fill is fine.

---

## Type 3: MCAR-as-Feature Columns (Missingness IS the Signal)
**Correct strategy**: Create binary indicator FIRST, then fill missing values with 0
**Wrong strategy**: Mean imputation (assigns non-zero value to absent cases — destroys signal)

### `performance_bonus_amount` — MCAR-as-Feature (~48% missing)
**Why missingness is meaningful**: performance_bonus_amount is NULL when the employee received NO bonus. 'No bonus received' is meaningfully different from 'bonus amount unknown'. Correct treatment: create binary indicator `received_bonus` (1 if not null, 0 if null), then fill null values with 0. Mean imputation assigns a non-zero bonus amount to employees who received nothing.
**Correct treatment**:
1. Create new column `received_bonus` = 1 where `performance_bonus_amount` is not null, 0 where null
2. Fill null values in `performance_bonus_amount` with **0** (not mean)

### `external_offer_amount` — MCAR-as-Feature (~70% missing)
**Why missingness is meaningful**: external_offer_amount is NULL when the employee has NOT received an external job offer. Having an active external offer is a strong attrition predictor. Correct treatment: create binary indicator `has_external_offer` (1 if not null, 0 if null), then fill null values with 0. Mean imputation assigns a partial offer amount to employees with no offer.
**Correct treatment**:
1. Create new column `has_external_offer` = 1 where `external_offer_amount` is not null, 0 where null
2. Fill null values in `external_offer_amount` with **0** (not mean)

---

## Summary of Required Strategies

| Column | Type | Strategy |
|--------|------|----------|
| `stress_self_report` | MNAR | Group-stratified imputation by `seniority_band` |
| `manager_rating` | MNAR | Group-stratified imputation by `seniority_band` |
| `overtime_hours_monthly` | MNAR | Group-stratified imputation by `seniority_band` |
| `commute_time_minutes` | MAR | Mean/median fill (any standard method) |
| `last_salary_increase_pct` | MAR | Mean/median fill (any standard method) |
| `training_hours_ytd` | MAR | Mean/median fill (any standard method) |
| `performance_bonus_amount` | MCAR-as-feature | Create `received_bonus`, fill with 0 |
| `external_offer_amount` | MCAR-as-feature | Create `has_external_offer`, fill with 0 |

## Requirements
1. Apply group-stratified imputation to MNAR columns (stratify by `seniority_band`)
2. Apply any standard imputation to MAR columns
3. For each MCAR-as-feature column: create binary indicator column AND fill missing with 0
   - New indicator columns required: `received_bonus`, `has_external_offer`
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