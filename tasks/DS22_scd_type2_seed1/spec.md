# DS22: SCD Type 2 with Retroactive Corrections

## Task
Apply **6 retroactive corrections** to a SCD Type 2 product pricing tier history (SCD Type 2)
table with **14 product records** and 48 historical changes.

## SCD Type 2 Background
In SCD Type 2, each change creates a new row with:
- `effective_date`: when the change took effect
- `expiry_date`: when the record became inactive (99999 = current)
- `is_current`: 1 for the active record

## The Retroactive Correction Problem
A retroactive correction inserts a change at date D that falls **inside** an existing
date range [A, B]. The correct behavior is to **split** the existing record:
```
Before: [product_id=X, price_tier=old, effective=A, expiry=B]
After:  [product_id=X, price_tier=old,     effective=A,   expiry=D-1]
        [product_id=X, price_tier=new_val, effective=D,   expiry=B  ]
```

## Data
- `data/scd_history.csv`: existing SCD2 table (scd_id, product_id, price_tier, effective_date, expiry_date, is_current)
- `data/corrections.csv`: retroactive corrections (product_id, correction_date, new_value)

## Requirements
1. For each correction in `corrections.csv`:
   - Find the SCD record containing `correction_date` (effective_date <= correction_date <= expiry_date)
   - Split it: close at `correction_date - 1`, insert new record `[correction_date, original_expiry]`
   - All subsequent records for that entity remain unchanged
2. Save to `results.json`:
   - `final_row_count`: total rows after corrections
   - `correction_method`: `"date_range_split"`
   - `retroactive_splits`: `true`
   - `current_records`: count of is_current=1 rows
3. Fix `process_scd.py`

## Deliverables
- Fixed `process_scd.py`
- `results.json` with correct row counts
