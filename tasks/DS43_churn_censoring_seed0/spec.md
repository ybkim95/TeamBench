# DS43: Churn Prediction with Informative Censoring

## Task
Compute the **churn rate** for SaaS tier subscription churn analysis with **732 customers**
over **12 months**.

## The Problem: Informative Censoring
Customers who **upgrade** their plan are **right-censored** — they leave the at-risk
pool at their upgrade time. They did NOT churn, but they also cannot be treated as
"survived" because their departure is not random (upgraders are more engaged).

**Naive approach (wrong)**: `churn_rate = n_churned / n_total`
This includes upgraders in the denominator as if they were at risk for the full period.

**Correct approach**: Exclude upgraders from both numerator and denominator:
```
churn_rate = n_churned / (n_total - n_upgraded)
```

## Data
File: `data/subscriptions.csv`
- `account_id`: customer identifier
- `event_type`: `"cancellation"` | `"plan_upgrade"` | `"active"`
- `churned`: 1 if churned, 0 otherwise
- `upgraded`: 1 if upgraded (censored), 0 otherwise
- `observed_months`: months observed before event or end of period

## Requirements
1. Load `data/subscriptions.csv`
2. Count `n_churned` = sum of `churned` column
3. Count `n_upgraded` = sum of `upgraded` column (these are censored)
4. Compute `n_at_risk` = `n_total - n_upgraded`
5. Compute `churn_rate` = `n_churned / n_at_risk`
6. Save to `results.json`:
   - `n_at_risk`: customers at risk (excluding upgraders)
   - `churn_rate`: correct churn rate
   - `censoring_handled`: `true`
7. Fix `churn_analysis.py`

## Expected Results
- Correct churn rate ≈ 0.2525
- Buggy (naive) churn rate ≈ 0.2063 (understated — 134 upgraders inflate denominator)

## Deliverables
- Fixed `churn_analysis.py`
- `results.json` with correct churn rate excluding censored upgraders
