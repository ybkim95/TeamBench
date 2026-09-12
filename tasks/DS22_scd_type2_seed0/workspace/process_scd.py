"""
SCD Type 2 processor for employee department history (SCD Type 2).
BUG: Applies retroactive corrections by closing current record and appending new one,
but does NOT split existing date ranges when correction falls in the middle.
A correction at date D within range [A, B] should produce:
  [A, D-1] original_value
  [D, B]   new_value
Instead this script only appends at the end, leaving gaps and wrong date ranges.
"""
import pandas as pd
import json

scd = pd.read_csv("data/scd_history.csv")
corrections = pd.read_csv("data/corrections.csv")

scd = scd.copy()

for _, corr in corrections.iterrows():
    eid = corr["employee_id"]
    corr_date = int(corr["correction_date"])
    new_val = corr["new_value"]

    # BUG: finds current record and closes it, but ignores records in between
    # Should split the record that CONTAINS corr_date into two parts
    mask = (scd["employee_id"] == eid) & (scd["is_current"] == 1)
    if mask.any():
        # BUG: always closes current, regardless of whether corr_date is retroactive
        scd.loc[mask, "expiry_date"] = corr_date - 1
        scd.loc[mask, "is_current"] = 0
        # Append new current record (BUG: effective_date should be corr_date, expiry 99999)
        new_row = {
            "scd_id": scd["scd_id"].max() + 1,
            "employee_id": eid,
            "department": new_val,
            "effective_date": corr_date,
            "expiry_date": 99999,
            "is_current": 1,
        }
        scd = pd.concat([scd, pd.DataFrame([new_row])], ignore_index=True)

results = {
    "final_row_count": len(scd),
    "correction_method": "append_only",  # BUG: should be "date_range_split"
    "retroactive_splits": False,          # BUG: should be True
    "current_records": int((scd["is_current"] == 1).sum()),
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"SCD rows: {len(scd)}, current: {results['current_records']}")
print("WARNING: Corrections not properly split into date ranges!")
