# DS5: Outlier vs Signal

## Task
Apply correct outlier treatment to the **financial transaction anomaly dataset** dataset.
Dataset: `data/dataset.csv`

## Context
The anomaly detector identified 6 outlier groups. Each group requires a
DIFFERENT treatment. A blanket 'remove all outliers' strategy will FAIL —
it removes genuine signal groups and eliminates the ambiguous group that
must be flagged for human review.

## Outlier Group Classification

### Group 1: `institutional_trade` (42 rows) — KEEP
**Description**: large institutional block trades — legitimate high-value transactions
**Treatment**: **KEEP**
**Rationale**: Institutional block trades are pre-approved, documented transactions from verified counterparties. Removing them would eliminate the entire institutional segment from the model training data.

### Group 2: `test_transaction` (40 rows) — REMOVE
**Description**: QA test transactions with amounts ending in exactly .000000
**Treatment**: **REMOVE**
**Rationale**: Sub-dollar test transactions are confirmed QA artifacts (logged in the test harness). They are not real financial activity.

### Group 3: `settlement_batch` (56 rows) — KEEP
**Description**: end-of-day settlement batches — large legitimate clearing transactions
**Treatment**: **KEEP**
**Rationale**: Settlement batches are end-of-day clearing transactions documented in the operations manual. The detector threshold (80k-250k) is too narrow and excludes the upper tail of legitimate large settlements (250k-300k). The correct threshold is 90k-320k.

**THRESHOLD BUG**: The current detector threshold for this group is
`80000` to `250000` — too aggressive.
The correct threshold is `90000` to
`320000`. Rows with `outlier_group == 'settlement_batch'`
and `transaction_amount` outside the correct range should be reviewed.
For this task, treat ALL rows labeled `settlement_batch` as KEEP (the label
reflects the corrected threshold).

### Group 4: `duplicate_entry` (27 rows) — REMOVE
**Description**: duplicate transaction entries from ETL double-processing bug
**Treatment**: **REMOVE**
**Rationale**: ETL duplicate entries are confirmed data quality defects (incident INC-2024-0892). The transactions exist twice in the database due to a reprocessing bug. One copy must be removed.

### Group 5: `fraud_attempt` (50 rows) — KEEP
**Description**: confirmed fraud attempts — high-value signal for fraud detection model
**Treatment**: **KEEP**
**Rationale**: Confirmed fraud attempts are the primary target class. Removing them from training data would eliminate the most informative positive-class examples.

### Group 6: `cross_border_unusual` (37 rows) — FLAG (do NOT remove)
**Description**: cross-border transactions with unusual currency conversion patterns — ambiguous legitimacy
**Treatment**: **FLAG**
**Rationale**: Cross-border unusual transactions have been referred to the compliance team for review but not conclusively classified as fraudulent or legitimate. Spec decision: create binary indicator `compliance_flag` (1=referred) and KEEP rows. Do NOT remove pending review.

**Action**: Add column `compliance_flag` = 1 for all rows in this
group, then KEEP them in the output. Do NOT remove them.

## Treatment Summary

| Group | Label | Count | Treatment |
|-------|-------|-------|-----------|
| 1 | `institutional_trade` | 42 | KEEP |
| normal | normal | 1734 | KEEP |
| 2 | `test_transaction` | 40 | REMOVE |
| normal | normal | 1734 | KEEP |
| 3 | `settlement_batch` | 56 | KEEP |
| normal | normal | 1734 | KEEP |
| 4 | `duplicate_entry` | 27 | REMOVE |
| normal | normal | 1734 | KEEP |
| 5 | `fraud_attempt` | 50 | KEEP |
| normal | normal | 1734 | KEEP |
| 6 | `cross_border_unusual` | 37 | FLAG + KEEP (add indicator column) |
| normal | normal | 1734 | KEEP |

## Requirements
1. **KEEP** rows where `outlier_group` is `1` (`institutional_trade`), `3` (`settlement_batch`), `5` (`fraud_attempt`)
2. **REMOVE** rows where `outlier_group` is `2` (`test_transaction`), `4` (`duplicate_entry`)
3. **FLAG** rows where `outlier_group` is `6` (`cross_border_unusual`): add column `compliance_flag` = 1, keep in output
4. For all other rows: set `compliance_flag` = 0
5. Save cleaned dataset to `data/cleaned.csv` (expected: ~1919 rows)
6. Save stats to `cleaning_stats.json` with keys:
   - `cleaned_rows`, `removed_rows`
   - `group_1_kept`, `group_3_kept`, `group_5_kept` (must be > 0)
   - `group_2_removed`, `group_4_removed` (must equal original counts)
   - `compliance_flag_flagged` (must equal count of group 6 rows)
7. Script: `clean.py`

## Grading Note
The grader checks BOTH under-fixing AND over-fixing:
- Signal groups (1, 3, 5) present in cleaned output: +2 pts each
- Error groups (2, 4) absent from cleaned output: +2 pts each
- Group 6 present AND `compliance_flag` column created: +3 pts
- **Group 6 absent from cleaned output: -3 pts** (over-removal)
- Signal groups absent: -2 pts each (over-removal)

## Deliverables
- Fixed `clean.py`
- `data/cleaned.csv` with ~1919 rows and `compliance_flag` column
- `cleaning_stats.json`