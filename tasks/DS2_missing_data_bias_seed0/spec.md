# DS2: Missing Data Bias

## Task
Apply correct missing data imputation to the **hospital patient readmission risk dataset** dataset.
File: `data/dataset.csv` (1894 rows)

## CRITICAL: Different Columns Require Different Strategies

The dataset has 8 columns with missing values across 3 missingness types.
A single global-mean-fill strategy is WRONG for 5 of the 8 columns.

---

## Type 1: MNAR Columns (Missing Not At Random)
**Correct strategy**: Group-stratified median/bound imputation by `severity_level`
**Wrong strategy**: Global mean fill (introduces systematic bias)

### `pain_score` — MNAR (~36% missing)
**Mechanism**: Patients in severe pain are less able to complete pain surveys. High pain scores (>7) are systematically missing. Global mean imputation underestimates pain for the most critical patients.
**Correct imputation**: group-median imputation by severity_level
Group-level median estimates by `severity_level` (mild, moderate, severe, critical):
impute missing values within each group using that group's median (or appropriate bound).

### `functional_score` — MNAR (~36% missing)
**Mechanism**: Patients with very low functional ability (score <20) often cannot participate in functional assessments. Low scores are selectively missing. Mean imputation overestimates functional ability for the sickest patients.
**Correct imputation**: lower-bound imputation using minimum observed per severity group
Group-level median estimates by `severity_level` (mild, moderate, severe, critical):
impute missing values within each group using that group's median (or appropriate bound).

### `discharge_readiness` — MNAR (~36% missing)
**Mechanism**: Clinical staff only complete discharge readiness assessments for patients deemed likely to be discharged soon. Patients with high readiness scores are assessed more often, but low-readiness patients are systematically skipped. Global mean overestimates discharge readiness.
**Correct imputation**: stratified median imputation by severity_level
Group-level median estimates by `severity_level` (mild, moderate, severe, critical):
impute missing values within each group using that group's median (or appropriate bound).

---

## Type 2: MAR Columns (Missing At Random)
**Correct strategy**: Global mean or median fill — any standard imputation is acceptable

### `specialist_referral_count` — MAR (~15% missing)
**Mechanism**: Younger patients (age < 40) are less likely to have specialist referrals recorded. Missingness depends on observed age, not on the referral count itself. Median fill is acceptable.
**Imputation**: Global mean or median fill is fine.

### `comorbidity_index` — MAR (~12% missing)
**Mechanism**: Comorbidity index is missing for patients admitted through the emergency pathway (observed field). Missingness depends on admission route, not on the index value. Mean fill is acceptable.
**Imputation**: Global mean or median fill is fine.

### `lab_result_glucose` — MAR (~18% missing)
**Mechanism**: Glucose lab results are missing for patients who had same-day discharge (observed field). Missingness depends on length of stay, not glucose level. Mean fill is acceptable.
**Imputation**: Global mean or median fill is fine.

---

## Type 3: MCAR-as-Feature Columns (Missingness IS the Signal)
**Correct strategy**: Create binary indicator FIRST, then fill missing values with 0
**Wrong strategy**: Mean imputation (assigns non-zero value to absent cases — destroys signal)

### `imaging_order_flag` — MCAR-as-Feature (~40% missing)
**Why missingness is meaningful**: imaging_order_flag is NULL when NO imaging was ordered. The absence itself means 'no imaging ordered' — a clinically meaningful distinction from 'imaging ordered, value unknown'. Correct treatment: create binary indicator `imaging_ordered` (1 if not null, 0 if null), then fill null values with 0. Mean imputation destroys this signal by filling NULLs with a fractional value.
**Correct treatment**:
1. Create new column `imaging_ordered` = 1 where `imaging_order_flag` is not null, 0 where null
2. Fill null values in `imaging_order_flag` with **0** (not mean)

### `prior_surgery_score` — MCAR-as-Feature (~45% missing)
**Why missingness is meaningful**: prior_surgery_score is NULL when the patient has NO prior surgical history. 'No prior surgery' is diagnostically meaningful — these patients have different risk profiles than patients with unknown surgery history. Correct treatment: create binary indicator `had_prior_surgery` (1 if not null, 0 if null), then fill null values with 0. Mean imputation assigns a non-zero surgery score to non-surgical patients.
**Correct treatment**:
1. Create new column `had_prior_surgery` = 1 where `prior_surgery_score` is not null, 0 where null
2. Fill null values in `prior_surgery_score` with **0** (not mean)

---

## Summary of Required Strategies

| Column | Type | Strategy |
|--------|------|----------|
| `pain_score` | MNAR | Group-stratified imputation by `severity_level` |
| `functional_score` | MNAR | Group-stratified imputation by `severity_level` |
| `discharge_readiness` | MNAR | Group-stratified imputation by `severity_level` |
| `specialist_referral_count` | MAR | Mean/median fill (any standard method) |
| `comorbidity_index` | MAR | Mean/median fill (any standard method) |
| `lab_result_glucose` | MAR | Mean/median fill (any standard method) |
| `imaging_order_flag` | MCAR-as-feature | Create `imaging_ordered`, fill with 0 |
| `prior_surgery_score` | MCAR-as-feature | Create `had_prior_surgery`, fill with 0 |

## Requirements
1. Apply group-stratified imputation to MNAR columns (stratify by `severity_level`)
2. Apply any standard imputation to MAR columns
3. For each MCAR-as-feature column: create binary indicator column AND fill missing with 0
   - New indicator columns required: `imaging_ordered`, `had_prior_surgery`
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