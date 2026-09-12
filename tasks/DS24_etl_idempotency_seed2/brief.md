# DS24: ETL Idempotency (Brief)

Build idempotent IoT sensor reading ETL pipeline.
Fix `etl.py` — add checkpoint file + upsert semantics.
Running twice must produce same row count.
Save results to `results.json`.
