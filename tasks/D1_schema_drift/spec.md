# D1: Schema Drift ETL Repair

## Goal
Fix the ETL pipeline so it correctly processes all input CSV files despite schema changes.

## Hard Requirements

1. The pipeline reads CSV files from `data/input/` and writes a single `data/output/result.csv`.
2. Input files have varying schemas across 5 batches:
   - `batch_001.csv`: columns `[id, name, value]`
   - `batch_002.csv`: columns `[id, name, value, category]` (new column added)
   - `batch_003.csv`: columns `[id, full_name, value, category]` (column renamed: `name` -> `full_name`)
   - `batch_004.csv`: columns `[record_id, name, amount, category, region]` (multiple renames + extra column)
   - `batch_005.csv`: columns `[id, name, value, category, _timestamp]` (extra metadata column + duplicates)
3. Column mappings:
   - `full_name` must be mapped to `name`
   - `record_id` must be mapped to `id`
   - `amount` must be mapped to `value`
4. Output `result.csv` must have columns: `[id, name, value, category]` -- exact order.
   - Drop any columns NOT in the canonical schema (e.g., `region`, `_timestamp`)
5. Missing `category` values must be filled with `"unknown"`.
6. Handle duplicate `id`s: keep the row with the HIGHER `value`. If values are equal, keep the last occurrence.
7. Rows where `value` is non-numeric or negative: replace `value` with `0`.
8. Output must be sorted by `category` ascending, then by `id` ascending (numeric sort).
9. No duplicate rows allowed (by `id`).
10. The pipeline script is `etl.py` -- run with `python etl.py`.

## Deliverables
- Fixed `etl.py` in workspace.
- Verifier must verify output schema, row count, sort order, dedup, and produce attestation.
