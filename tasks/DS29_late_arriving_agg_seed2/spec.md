# DS29: Incremental Aggregation with Late-Arriving Data

## Task
Maintain a weekly units_sold aggregate over 5 windows
(60 initial records), then apply 6 late-arriving corrections.

## The Late-Arriving Data Problem
When a correction arrives for a past window, it **replaces** an existing record.
The correct formula is:
```
agg[window] = agg[window] - old_value + new_value
```

The buggy approach adds the new value without subtracting the old:
```
agg[window] = agg[window] + new_value  # WRONG — double-counts old value
```

## Data
- `data/initial_records.csv`: record_id, report_week, units_sold
- `data/corrections.csv`: record_id, report_week, units_sold, original_id, old_value

## Requirements
1. Load initial records and compute per-window sums
2. For each correction:
   - Apply: `agg[window] -= old_value; agg[window] += new_value`
   - Write audit entry: `{window, old_value, new_value, original_id, correction_id}`
3. Write audit trail to `audit_log.json` (list of correction entries)
4. Save to `results.json`:
   - `aggregates`: dict of report_week → corrected sum
   - `n_windows`: 5
   - `n_corrections_applied`: 6
   - `audit_entries_written`: 6
   - `double_counting_fixed`: `true`
5. Fix `aggregate.py`

## Deliverables
- Fixed `aggregate.py`
- `audit_log.json` with 6 entries
- `results.json`
