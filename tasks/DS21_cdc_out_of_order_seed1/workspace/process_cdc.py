"""
CDC stream processor for user profile change data capture stream.
BUG: Processes events in arrival_time order instead of event_time order.
This means late-arriving events (which have earlier event_times but later
arrival_times) overwrite newer state, corrupting the final snapshot.

Fix: Sort events by event_time before processing. For upsert semantics,
only apply an event if its event_time is >= the current record's last_event_time.
"""
import pandas as pd
import json

df = pd.read_csv("data/cdc_events.csv")

# BUG: sorting by arrival_time instead of event_time
# Late-arriving events with earlier event_times will incorrectly overwrite newer state
df = df.sort_values("arrival_time")  # BUG: should be event_time

final_state = {}

for _, row in df.iterrows():
    eid = row["user_id"]
    op = row["op"]

    if op == "DELETE":
        final_state.pop(eid, None)
    else:
        # BUG: no last-writer-wins check — always overwrites
        final_state[eid] = {
            "account_status": row["account_status"],
            "balance": float(row["balance"]),
            "last_event_time": int(row["event_time"]),
        }

results = {
    "final_record_count": len(final_state),
    "processing_order": "arrival_time",  # BUG: should be event_time
    "upsert_semantics": False,            # BUG: should be True
    "final_state": final_state,
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Processed {len(df)} events -> {len(final_state)} final records")
print("WARNING: Used arrival_time ordering — may have stale records!")
