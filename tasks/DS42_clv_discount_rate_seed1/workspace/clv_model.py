"""
CLV model for retail customer lifetime value.
BUG: Applies annual discount rate (0.148) directly to monthly periods.
Monthly cashflows should use a monthly equivalent rate:
  monthly_rate = (1 + annual_rate)^(1/12) - 1

Applying annual rate to monthly periods massively under-discounts future cash
flows, overstating CLV. For a 12% annual rate, the monthly rate is ~0.949%
not 12%, making a huge difference over 24-48 periods.

Fix: Convert annual_rate to monthly_rate before computing NPV.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/customer_cashflows.csv")

ANNUAL_RATE = 0.148
# BUG: should convert to monthly rate first
# monthly_rate = (1 + ANNUAL_RATE) ** (1/12) - 1
DISCOUNT_RATE = ANNUAL_RATE  # BUG: using annual rate for monthly periods

clv_by_customer = {}
for cid, group in df.groupby("customer_id"):
    group = group.sort_values("month")
    npv = 0.0
    for _, row in group.iterrows():
        t = int(row["month"])
        cf = float(row["monthly_spend"])
        # BUG: (1 + annual_rate)^month instead of (1 + monthly_rate)^month
        npv += cf / ((1 + DISCOUNT_RATE) ** t)
    clv_by_customer[cid] = round(npv, 2)

total_clv = sum(clv_by_customer.values())
avg_clv = total_clv / len(clv_by_customer) if clv_by_customer else 0.0

results = {
    "discount_rate_used": DISCOUNT_RATE,
    "rate_type": "annual",          # BUG: should be "monthly_converted"
    "correctly_converted": False,   # BUG: should be True
    "n_customers": len(clv_by_customer),
    "total_clv": round(total_clv, 2),
    "avg_clv": round(avg_clv, 2),
    "clv_by_customer": clv_by_customer,
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Total CLV: {total_clv:.2f} (WARNING: using annual rate for monthly periods)")
print(f"Avg CLV per customer: {avg_clv:.2f}")
