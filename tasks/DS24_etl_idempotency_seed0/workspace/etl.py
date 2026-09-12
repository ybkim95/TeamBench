"""
ETL pipeline for sales transaction ETL pipeline.
BUG: No checkpoint — re-running after a partial failure duplicates already-processed
batches. Also uses plain INSERT which doesn't handle re-inserted records.

Fix:
1. Use a checkpoint file (checkpoint.json) to track completed batch_ids
2. Skip batches that are already in the checkpoint
3. Use upsert semantics (INSERT OR REPLACE) to avoid duplicates
"""
import pandas as pd
import json
import os
import sqlite3

df = pd.read_csv("data/source_records.csv")
conn = sqlite3.connect("output.db")
conn.execute("""
    CREATE TABLE IF NOT EXISTS records (
        transaction_id TEXT,
        amount REAL,
        batch_id INTEGER,
        processed_at INTEGER
    )
""")

# Simulate: pipeline previously failed at batch 5
# On re-run, batches 1..5 will be processed again
# BUG: no checkpoint check, no upsert — duplicates will be inserted

for batch_id in range(1, 8 + 1):
    batch_df = df[df["batch_id"] == batch_id]

    # BUG: no checkpoint check — always processes every batch
    # BUG: INSERT instead of INSERT OR REPLACE — duplicates on re-run
    for _, row in batch_df.iterrows():
        conn.execute(
            "INSERT INTO records VALUES (?, ?, ?, ?)",  # BUG: not upsert
            (row["transaction_id"], row["amount"], row["batch_id"], row["processed_at"])
        )
    conn.commit()
    # BUG: no checkpoint written

total_rows = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
conn.close()

results = {
    "total_rows_inserted": total_rows,
    "idempotent": False,       # BUG: should be True
    "checkpoint_used": False,  # BUG: should be True
    "upsert_used": False,      # BUG: should be True
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Inserted {total_rows} rows (may include duplicates!)")
