# DS7: Data Pipeline Repair

## Task
Fix the **user behavior event aggregation pipeline** pipeline with 4 known bugs.
Script: `pipeline.py`

## Input Files
- `data/events.csv` — 234 rows (main fact table)
- `data/users.csv` — 88 rows (dimension table)
- `data/sessions.csv` — product reference

## Bug Inventory

### Bug 1: Wrong Join Type
**Current**: `INNER JOIN` on `user_id`
**Problem**: Loses all events rows that have no matching users entry
**Fix**: Use `LEFT JOIN` — preserve all events rows, null-fill missing users fields

### Bug 2: Incorrect Aggregation
**Current**: `mean` for `total_engagement`
**Problem**: total_engagement must be a sum, not mean
**Fix**: Use `sum(event_value)` for `total_engagement`

### Bug 3: Timezone Conversion Missing
**Current**: Timestamps remain in `UTC`
**Business rule**: All output timestamps must be in `US/Pacific`
**Fix**: Convert `event_timestamp` from `UTC` to `US/Pacific`

### Bug 4: No Deduplication
**Current**: Duplicate `event_id` rows remain in output
**Rule**: keep first occurrence by event_timestamp
**Fix**: Deduplicate by `event_id` using the correct strategy

## Expected Output
- File: `data/output/result.csv`
- Row count: 234
- Total `event_value`: 557994.55
- `data/output/summary.json` with: `row_count`, `total_engagement`, `timezone="US/Pacific"`, `duplicates_removed=true`, `join_type="left"`

## Deliverables
- Fixed `pipeline.py`
- `data/output/result.csv` matching expected row count
- `data/output/summary.json` with correct metadata
