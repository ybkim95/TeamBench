"""
Data pipeline for user behavior event aggregation pipeline.
Contains 4 bugs:
  BUG 1: INNER JOIN — loses orphan rows (should be LEFT JOIN)
  BUG 2: Uses mean for total_engagement (should be sum)
  BUG 3: Timezone not converted from UTC to US/Pacific
  BUG 4: No deduplication by event_id
"""
import pandas as pd
import os
import json

os.makedirs("data/output", exist_ok=True)

orders = pd.read_csv("data/events.csv")
customers = pd.read_csv("data/users.csv")

print(f"Orders: {len(orders)} rows")
print(f"Customers: {len(customers)} rows")

# BUG 1: INNER JOIN loses rows with no matching customer
merged = orders.merge(customers, on="user_id", how="inner")  # BUG: should be left
print(f"After join: {len(merged)} rows (inner join lost {len(orders) - len(merged)} rows)")

# BUG 2: Wrong aggregation
total_engagement = merged["event_value"].astype(float).mean()  # BUG: should be sum
print(f"total_engagement (mean): {total_engagement:.2f}")

# BUG 3: No timezone conversion
# merged["event_timestamp"] should be converted from UTC to US/Pacific
# but we skip this conversion
print(f"Timestamps remain in UTC (not converted to US/Pacific)")

# BUG 4: No deduplication
# merged may contain duplicate event_id rows
print(f"Duplicate event_ids: {merged['event_id'].duplicated().sum()}")

# Save output (with all bugs)
merged.to_csv("data/output/result.csv", index=False)

summary = {
    "total_engagement": float(total_engagement),
    "row_count": len(merged),
    "timezone": "UTC",  # BUG: should be US/Pacific
    "duplicates_removed": False,  # BUG: should be True
    "join_type": "inner",  # BUG: should be left
}
with open("data/output/summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("Saved data/output/result.csv and data/output/summary.json")
