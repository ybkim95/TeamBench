# DS29: Incremental Aggregation with Late-Arriving Data

## Task
Maintain a dayly revenue aggregate over 8 windows
(184 initial records), then apply 5 late-arriving corrections.

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
- `data/initial_records.csv`: sale_id, sale_date, revenue
- `data/corrections.csv`: sale_id, sale_date, revenue, original_id, old_value

## Requirements
1. Load initial records and compute per-window sums
2. For each correction:
   - Apply: `agg[window] -= old_value; agg[window] += new_value`
   - Write audit entry: `{window, old_value, new_value, original_id, correction_id}`
3. Write audit trail to `audit_log.json` (list of correction entries)
4. Save to `results.json`:
   - `aggregates`: dict of sale_date → corrected sum
   - `n_windows`: 8
   - `n_corrections_applied`: 5
   - `audit_entries_written`: 5
   - `double_counting_fixed`: `true`
5. Fix `aggregate.py`

## Deliverables
- Fixed `aggregate.py`
- `audit_log.json` with 5 entries
- `results.json`
