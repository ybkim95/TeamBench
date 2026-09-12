# DS29: Incremental Aggregation with Late-Arriving Data

## Task
Maintain a hourly event_count aggregate over 6 windows
(72 initial records), then apply 9 late-arriving corrections.

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
- `data/initial_records.csv`: event_id, metric_hour, event_count
- `data/corrections.csv`: event_id, metric_hour, event_count, original_id, old_value

## Requirements
1. Load initial records and compute per-window sums
2. For each correction:
   - Apply: `agg[window] -= old_value; agg[window] += new_value`
   - Write audit entry: `{window, old_value, new_value, original_id, correction_id}`
3. Write audit trail to `audit_log.json` (list of correction entries)
4. Save to `results.json`:
   - `aggregates`: dict of metric_hour → corrected sum
   - `n_windows`: 6
   - `n_corrections_applied`: 9
   - `audit_entries_written`: 9
   - `double_counting_fixed`: `true`
5. Fix `aggregate.py`

## Deliverables
- Fixed `aggregate.py`
- `audit_log.json` with 9 entries
- `results.json`
