# DS7: Data Pipeline Repair

## Task
Fix the **inventory reconciliation pipeline** pipeline with 4 known bugs.
Script: `pipeline.py`

## Input Files
- `data/transactions.csv` — 214 rows (main fact table)
- `data/warehouses.csv` — 91 rows (dimension table)
- `data/items.csv` — product reference

## Bug Inventory

### Bug 1: Wrong Join Type
**Current**: `INNER JOIN` on `warehouse_id`
**Problem**: Loses all transactions rows that have no matching warehouses entry
**Fix**: Use `LEFT JOIN` — preserve all transactions rows, null-fill missing warehouses fields

### Bug 2: Incorrect Aggregation
**Current**: `count` for `total_units`
**Problem**: total_units must be a sum, not count
**Fix**: Use `sum(quantity)` for `total_units`

### Bug 3: Timezone Conversion Missing
**Current**: Timestamps remain in `UTC`
**Business rule**: All output timestamps must be in `Europe/London`
**Fix**: Convert `transaction_timestamp` from `UTC` to `Europe/London`

### Bug 4: No Deduplication
**Current**: Duplicate `transaction_id` rows remain in output
**Rule**: keep highest quantity by transaction_id
**Fix**: Deduplicate by `transaction_id` using the correct strategy

## Expected Output
- File: `data/output/result.csv`
- Row count: 214
- Total `quantity`: 542801.79
- `data/output/summary.json` with: `row_count`, `total_units`, `timezone="Europe/London"`, `duplicates_removed=true`, `join_type="left"`

## Deliverables
- Fixed `pipeline.py`
- `data/output/result.csv` matching expected row count
- `data/output/summary.json` with correct metadata
