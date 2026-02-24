# D2: Data Quality + Spec Compliance

## Goal
Process the input dataset and produce output that satisfies ALL quality rules.

## Hard Requirements

1. Read `data/input/records.csv` and produce `data/output/clean.csv`.
2. Script: `python clean.py`
3. Quality rules:
   - **Missing values**: Any cell with empty string or `"N/A"` must be replaced with `"MISSING"`.
   - **Sort order**: Output must be sorted by `score` descending, then by `name` ascending (alphabetical).
   - **Deduplication**: Rows with the same `id` must be deduplicated, keeping the row with the higher `score`.
   - **Range check**: `score` must be between 0 and 100 inclusive. Rows outside this range must be dropped entirely.
   - **Department correction**: Rows where `department` is `"MISSING"` AND `score` is less than 50 should have `department` set to `"review_needed"` instead of `"MISSING"`.
4. Output columns: `[id, name, score, department]` — exact order.
5. No header row modifications (keep original column names).
6. Output must use UTF-8 encoding with Unix line endings.

## Deliverables
- Fixed `clean.py` in workspace.
- Verifier must confirm all quality rules and produce attestation.
