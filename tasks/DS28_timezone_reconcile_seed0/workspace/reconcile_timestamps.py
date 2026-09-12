"""
Timestamp reconciliation for financial trade timestamp reconciliation.
BUG 1: Source C uses epoch offset = 0 (Unix epoch) instead of
       946684800 (Y2K epoch (2000-01-01)), making all C timestamps wrong by
       946684800 seconds.
BUG 2: Source B local_time column stores raw Unix timestamps with a timezone label,
       but this script incorrectly adds a fixed UTC offset instead of using pytz
       for DST-aware conversion.

Fix:
1. Source C: subtract 946684800 (not 0) to get UTC
2. Source B: use pytz.timezone('US/Eastern') + localize() for DST-aware conversion
"""
import pandas as pd
import json

df_a = pd.read_csv("data/exchange_feed.csv")
df_b = pd.read_csv("data/broker_system.csv")
df_c = pd.read_csv("data/clearing_house.csv")

# Source A: already UTC unix timestamps — correct
df_a["utc_ts"] = df_a["unix_ts"].astype(int)

# BUG: Source B — fixed offset instead of DST-aware conversion
# Assuming US/Eastern is always UTC-5 (ignores DST, wrong half the year)
UTC_OFFSET_HOURS = -5  # BUG: hardcoded, ignores DST
df_b["utc_ts"] = df_b["local_time"].astype(int) - (UTC_OFFSET_HOURS * 3600)  # BUG

# BUG: Source C — using Unix epoch (0) instead of Y2K epoch (2000-01-01) (946684800)
EPOCH_C_OFFSET = 0  # BUG: should be 946684800
df_c["utc_ts"] = df_c["custom_ts"].astype(int) + EPOCH_C_OFFSET  # BUG

# Combine
df_a["source"] = "exchange_feed"
df_b["source"] = "broker_system"
df_c["source"] = "clearing_house"

combined = pd.concat([
    df_a[["id", "utc_ts", "price", "source"]],
    df_b[["id", "utc_ts", "price", "source"]],
    df_c[["id", "utc_ts", "price", "source"]],
], ignore_index=True)

combined.to_csv("data/reconciled.csv", index=False)

results = {
    "total_records": len(combined),
    "sources": ["exchange_feed", "broker_system", "clearing_house"],
    "epoch_c_offset_used": EPOCH_C_OFFSET,  # BUG: wrong
    "tz_b_dst_aware": False,                # BUG: should be True
    "reconciliation_correct": False,        # BUG
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Reconciled {len(combined)} records. WARNING: timestamps may be wrong!")
