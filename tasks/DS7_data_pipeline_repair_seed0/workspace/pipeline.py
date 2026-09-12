"""
Data pipeline for sales order processing pipeline.
Contains 4 bugs:
  BUG 1: INNER JOIN — loses orphan rows (should be LEFT JOIN)
  BUG 2: Uses mean for total_revenue (should be sum)
  BUG 3: Timezone not converted from UTC to US/Eastern
  BUG 4: No deduplication by order_id
"""
import pandas as pd
import os
import json

os.makedirs("data/output", exist_ok=True)

orders = pd.read_csv("data/orders.csv")
customers = pd.read_csv("data/customers.csv")

print(f"Orders: {len(orders)} rows")
print(f"Customers: {len(customers)} rows")

# BUG 1: INNER JOIN loses rows with no matching customer
merged = orders.merge(customers, on="customer_id", how="inner")  # BUG: should be left
print(f"After join: {len(merged)} rows (inner join lost {len(orders) - len(merged)} rows)")

# BUG 2: Wrong aggregation
total_revenue = merged["order_amount"].astype(float).mean()  # BUG: should be sum
print(f"total_revenue (mean): {total_revenue:.2f}")

# BUG 3: No timezone conversion
# merged["order_timestamp"] should be converted from UTC to US/Eastern
# but we skip this conversion
print(f"Timestamps remain in UTC (not converted to US/Eastern)")

# BUG 4: No deduplication
# merged may contain duplicate order_id rows
print(f"Duplicate order_ids: {merged['order_id'].duplicated().sum()}")

# Save output (with all bugs)
merged.to_csv("data/output/result.csv", index=False)

summary = {
    "total_revenue": float(total_revenue),
    "row_count": len(merged),
    "timezone": "UTC",  # BUG: should be US/Eastern
    "duplicates_removed": False,  # BUG: should be True
    "join_type": "inner",  # BUG: should be left
}
with open("data/output/summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("Saved data/output/result.csv and data/output/summary.json")
