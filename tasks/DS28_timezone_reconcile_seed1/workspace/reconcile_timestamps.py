"""
Timestamp reconciliation for IoT sensor timestamp reconciliation.
BUG 1: Source C uses epoch offset = 0 (Unix epoch) instead of
       315532800 (GPS epoch (1980-01-06)), making all C timestamps wrong by
       315532800 seconds.
BUG 2: Source B local_time column stores raw Unix timestamps with a timezone label,
       but this script incorrectly adds a fixed UTC offset instead of using pytz
       for DST-aware conversion.

Fix:
1. Source C: subtract 315532800 (not 0) to get UTC
2. Source B: use pytz.timezone('Europe/Berlin') + localize() for DST-aware conversion
"""
import pandas as pd
import json

df_a = pd.read_csv("data/cloud_gateway.csv")
df_b = pd.read_csv("data/local_controller.csv")
df_c = pd.read_csv("data/embedded_firmware.csv")

# Source A: already UTC unix timestamps — correct
df_a["utc_ts"] = df_a["unix_ts"].astype(int)

# BUG: Source B — fixed offset instead of DST-aware conversion
# Assuming Europe/Berlin is always UTC-5 (ignores DST, wrong half the year)
UTC_OFFSET_HOURS = -5  # BUG: hardcoded, ignores DST
df_b["utc_ts"] = df_b["local_time"].astype(int) - (UTC_OFFSET_HOURS * 3600)  # BUG

# BUG: Source C — using Unix epoch (0) instead of GPS epoch (1980-01-06) (315532800)
EPOCH_C_OFFSET = 0  # BUG: should be 315532800
df_c["utc_ts"] = df_c["custom_ts"].astype(int) + EPOCH_C_OFFSET  # BUG

# Combine
df_a["source"] = "cloud_gateway"
df_b["source"] = "local_controller"
df_c["source"] = "embedded_firmware"

combined = pd.concat([
    df_a[["id", "utc_ts", "measurement", "source"]],
    df_b[["id", "utc_ts", "measurement", "source"]],
    df_c[["id", "utc_ts", "measurement", "source"]],
], ignore_index=True)

combined.to_csv("data/reconciled.csv", index=False)

results = {
    "total_records": len(combined),
    "sources": ["cloud_gateway", "local_controller", "embedded_firmware"],
    "epoch_c_offset_used": EPOCH_C_OFFSET,  # BUG: wrong
    "tz_b_dst_aware": False,                # BUG: should be True
    "reconciliation_correct": False,        # BUG
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Reconciled {len(combined)} records. WARNING: timestamps may be wrong!")
