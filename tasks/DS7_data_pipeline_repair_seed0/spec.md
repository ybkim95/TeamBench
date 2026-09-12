# DS7: Data Pipeline Repair

## Task
Fix the **sales order processing pipeline** pipeline with 4 known bugs.
Script: `pipeline.py`

## Input Files
- `data/orders.csv` — 298 rows (main fact table)
- `data/customers.csv` — 133 rows (dimension table)
- `data/products.csv` — product reference

## Bug Inventory

### Bug 1: Wrong Join Type
**Current**: `INNER JOIN` on `customer_id`
**Problem**: Loses all orders rows that have no matching customers entry
**Fix**: Use `LEFT JOIN` — preserve all orders rows, null-fill missing customers fields

### Bug 2: Incorrect Aggregation
**Current**: `mean` for `total_revenue`
**Problem**: total_revenue must be a sum, not mean
**Fix**: Use `sum(order_amount)` for `total_revenue`

### Bug 3: Timezone Conversion Missing
**Current**: Timestamps remain in `UTC`
**Business rule**: All output timestamps must be in `US/Eastern`
**Fix**: Convert `order_timestamp` from `UTC` to `US/Eastern`

### Bug 4: No Deduplication
**Current**: Duplicate `order_id` rows remain in output
**Rule**: keep latest by order_timestamp
**Fix**: Deduplicate by `order_id` using the correct strategy

## Expected Output
- File: `data/output/result.csv`
- Row count: 298
- Total `order_amount`: 711867.45
- `data/output/summary.json` with: `row_count`, `total_revenue`, `timezone="US/Eastern"`, `duplicates_removed=true`, `join_type="left"`

## Deliverables
- Fixed `pipeline.py`
- `data/output/result.csv` matching expected row count
- `data/output/summary.json` with correct metadata
