"""
Data pipeline for inventory reconciliation pipeline.
Contains 4 bugs:
  BUG 1: INNER JOIN — loses orphan rows (should be LEFT JOIN)
  BUG 2: Uses count for total_units (should be sum)
  BUG 3: Timezone not converted from UTC to Europe/London
  BUG 4: No deduplication by transaction_id
"""
import pandas as pd
import os
import json

os.makedirs("data/output", exist_ok=True)

orders = pd.read_csv("data/transactions.csv")
customers = pd.read_csv("data/warehouses.csv")

print(f"Orders: {len(orders)} rows")
print(f"Customers: {len(customers)} rows")

# BUG 1: INNER JOIN loses rows with no matching customer
merged = orders.merge(customers, on="warehouse_id", how="inner")  # BUG: should be left
print(f"After join: {len(merged)} rows (inner join lost {len(orders) - len(merged)} rows)")

# BUG 2: Wrong aggregation
total_units = merged["quantity"].astype(float).count()  # BUG: should be sum
print(f"total_units (count): {total_units:.2f}")

# BUG 3: No timezone conversion
# merged["transaction_timestamp"] should be converted from UTC to Europe/London
# but we skip this conversion
print(f"Timestamps remain in UTC (not converted to Europe/London)")

# BUG 4: No deduplication
# merged may contain duplicate transaction_id rows
print(f"Duplicate transaction_ids: {merged['transaction_id'].duplicated().sum()}")

# Save output (with all bugs)
merged.to_csv("data/output/result.csv", index=False)

summary = {
    "total_units": float(total_units),
    "row_count": len(merged),
    "timezone": "UTC",  # BUG: should be Europe/London
    "duplicates_removed": False,  # BUG: should be True
    "join_type": "inner",  # BUG: should be left
}
with open("data/output/summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("Saved data/output/result.csv and data/output/summary.json")
