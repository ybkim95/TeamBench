# DS24: ETL Idempotency (Brief)

Build idempotent log event ingestion pipeline.
Fix `etl.py` — add checkpoint file + upsert semantics.
Running twice must produce same row count.
Save results to `results.json`.
