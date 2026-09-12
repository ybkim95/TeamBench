# DS42: CLV Discount Rate Error (Monthly vs Annual Mismatch)

## Task
Compute **Customer Lifetime Value (CLV)** for 114 clients
using **35 months** of cashflow data in `financial services client CLV`.

## The Bug
The discount rate is specified as an **annual rate of 9.1%**, but cash flows
are **monthly**. The script incorrectly applies the annual rate directly to monthly
time periods, computing:

```
CLV = sum( CF_t / (1 + 0.091)^t )   # WRONG
```

The correct formula converts to a monthly equivalent rate first:
```
monthly_rate = (1 + 0.091)^(1/12) - 1  =  0.007284
CLV = sum( CF_t / (1 + 0.007284)^t )      # 
```

This error causes CLV to be **overstated by 0.42x**.

## Data
File: `data/customer_cashflows.csv`
- `client_id`: customer identifier
- `month`: period number (1-based)
- `monthly_revenue`: cash flow for this month

## Requirements
1. Load `data/customer_cashflows.csv`
2. Convert annual rate to monthly: `monthly_rate = (1 + 0.091)^(1/12) - 1`
3. Compute NPV per customer using monthly rate
4. Save to `results.json`:
   - `discount_rate_used`: the monthly rate (≈ 0.007284)
   - `rate_type`: `"monthly_converted"`
   - `correctly_converted`: `true`
   - `total_clv`: sum of all customer CLVs
   - `avg_clv`: average CLV per customer
   - `clv_by_customer`: dict mapping customer_id to CLV
5. Fix `clv_model.py`

## Expected Results
- Correct total CLV ≈ 757,917.13
- Buggy total CLV ≈ 315,192.49 (overstated by ~0.4x)

## Deliverables
- Fixed `clv_model.py`
- `results.json` with correct CLV using monthly discount rate
