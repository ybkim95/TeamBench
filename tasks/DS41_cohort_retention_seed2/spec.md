# DS41: Cohort Retention with Incomplete Cohorts

## Task
Compute a **6-period retention matrix** for e-commerce customer retention analysis
with **8 cohorts**.

## Problems in the Data
1. **Right-truncation**: The last 2 cohorts have not had enough time to be
   observed for all 6 periods. Including them deflates retention rates for
   later periods (they show 0 retention simply because the period hasn't occurred yet).
2. **Anomalous cohort**: Cohort index 1 has anomalously low retention
   (< 20% at period 1) due to a data quality issue and must be excluded.

## Data
File: `data/cohort_events.csv`
- `customer_id`: entity identifier
- `first_purchase_month`: cohort month (YYYY-MM)
- `period`: observation period (0 = signup, 1 = month 1, etc.)
- `active`: 1 if entity was active in this period

## Requirements
1. Load `data/cohort_events.csv`
2. Identify **right-truncated cohorts**: cohorts where `max(period) < 6`
3. Identify **anomalous cohorts**: cohorts where period-1 retention rate < 0.20
4. Exclude both truncated and anomalous cohorts from the retention matrix
5. Compute average retention by period on clean cohorts only
6. Save to `results.json`:
   - `n_cohorts_used`: count of clean cohorts used (should be 5)
   - `excluded_truncated`: `true`
   - `excluded_anomalous`: `true`
   - `avg_retention`: dict period_0 through period_6 for clean cohorts
   - `retention_matrix`: per-cohort retention rates (clean cohorts only)
7. Fix `retention.py`

## Expected Results
- Period-1 correct retention ≈ 0.706 (buggy: deflated by anomalous cohort)
- Period-3 correct retention ≈ 0.455
- Period-5 correct retention ≈ 0.333 (buggy: 0.294)

## Deliverables
- Fixed `retention.py`
- `results.json` with correct retention matrix
