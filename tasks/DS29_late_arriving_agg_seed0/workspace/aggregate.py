"""
Incremental aggregation for daily sales aggregation with late corrections.
BUG 1: Applies corrections by ADDING the new value to the existing aggregate,
       without subtracting the old value — causes double-counting.
BUG 2: No audit trail is written for corrections.

Fix:
1. For each correction: agg[window] = agg[window] - old_value + new_value
2. Write an audit trail entry for each correction to audit_log.json
"""
import pandas as pd
import json

df = pd.read_csv("data/initial_records.csv")
corrections = pd.read_csv("data/corrections.csv")

# Initial aggregation
agg = df.groupby("sale_date")["revenue"].sum().to_dict()
counts = df.groupby("sale_date")["revenue"].count().to_dict()

audit_log = []

for _, corr in corrections.iterrows():
    window = corr["sale_date"]
    new_val = float(corr["revenue"])
    old_val = float(corr["old_value"])

    # BUG: adds new value without subtracting old — double counts
    if window in agg:
        agg[window] = agg[window] + new_val  # BUG: should be agg[window] - old_val + new_val
    else:
        agg[window] = new_val

    # BUG: no audit trail entry written
    # Should append: {"window": window, "old_value": old_val, "new_value": new_val, ...}

# Write audit log (BUG: empty)
with open("audit_log.json", "w") as f:
    json.dump(audit_log, f, indent=2)

results = {
    "aggregates": {k: round(v, 4) for k, v in agg.items()},
    "n_windows": len(agg),
    "n_corrections_applied": len(corrections),
    "audit_entries_written": len(audit_log),  # BUG: 0
    "double_counting_fixed": False,            # BUG: should be True
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Aggregated {len(agg)} windows, {len(corrections)} corrections applied")
print(f"WARNING: Audit log empty, corrections double-counted!")
