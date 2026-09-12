# DS24: ETL Idempotency with Partial Failures

## Task
Build an idempotent IoT sensor reading ETL pipeline that processes 5 batches
of 22 records each (110 total records).

**Scenario**: The pipeline previously crashed after processing batch 2
of 5. On re-run, it must not duplicate already-processed records.

## The Idempotency Problem
A non-idempotent ETL:
1. Processes batches 1..2 successfully
2. Crashes at batch 3
3. On re-run: processes batches 1..2 AGAIN → duplicates!

## Requirements
1. Use a **checkpoint file** (`checkpoint.json`) tracking completed `batch_id`s
2. On each run: skip batches already in checkpoint
3. Use **upsert** (INSERT OR REPLACE) for `reading_id` as primary key
4. After each batch: write its `batch_id` to `checkpoint.json`
5. Save to `results.json`:
   - `total_rows_inserted`: final unique row count (should be exactly 110)
   - `idempotent`: `true`
   - `checkpoint_used`: `true`
   - `upsert_used`: `true`
6. Fix `etl.py`

## Verification
Running `etl.py` twice in a row should produce the same `total_rows_inserted = 110`.

## Deliverables
- Fixed `etl.py` with checkpoint + upsert
- `results.json`
- `output.db` with exactly 110 rows
