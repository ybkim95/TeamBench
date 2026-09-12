"""
Timestamp reconciliation for logistics event timestamp reconciliation.
BUG 1: Source C uses epoch offset = 0 (Unix epoch) instead of
       1072915200 (Custom epoch (2004-01-01)), making all C timestamps wrong by
       1072915200 seconds.
BUG 2: Source B local_time column stores raw Unix timestamps with a timezone label,
       but this script incorrectly adds a fixed UTC offset instead of using pytz
       for DST-aware conversion.

Fix:
1. Source C: subtract 1072915200 (not 0) to get UTC
2. Source B: use pytz.timezone('Asia/Tokyo') + localize() for DST-aware conversion
"""
import pandas as pd
import json

df_a = pd.read_csv("data/central_hub.csv")
df_b = pd.read_csv("data/regional_depot.csv")
df_c = pd.read_csv("data/rfid_scanner.csv")

# Source A: already UTC unix timestamps — correct
df_a["utc_ts"] = df_a["unix_ts"].astype(int)

# BUG: Source B — fixed offset instead of DST-aware conversion
# Assuming Asia/Tokyo is always UTC-5 (ignores DST, wrong half the year)
UTC_OFFSET_HOURS = -5  # BUG: hardcoded, ignores DST
df_b["utc_ts"] = df_b["local_time"].astype(int) - (UTC_OFFSET_HOURS * 3600)  # BUG

# BUG: Source C — using Unix epoch (0) instead of Custom epoch (2004-01-01) (1072915200)
EPOCH_C_OFFSET = 0  # BUG: should be 1072915200
df_c["utc_ts"] = df_c["custom_ts"].astype(int) + EPOCH_C_OFFSET  # BUG

# Combine
df_a["source"] = "central_hub"
df_b["source"] = "regional_depot"
df_c["source"] = "rfid_scanner"

combined = pd.concat([
    df_a[["id", "utc_ts", "weight_kg", "source"]],
    df_b[["id", "utc_ts", "weight_kg", "source"]],
    df_c[["id", "utc_ts", "weight_kg", "source"]],
], ignore_index=True)

combined.to_csv("data/reconciled.csv", index=False)

results = {
    "total_records": len(combined),
    "sources": ["central_hub", "regional_depot", "rfid_scanner"],
    "epoch_c_offset_used": EPOCH_C_OFFSET,  # BUG: wrong
    "tz_b_dst_aware": False,                # BUG: should be True
    "reconciliation_correct": False,        # BUG
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Reconciled {len(combined)} records. WARNING: timestamps may be wrong!")
