# DS26: Schema Evolution with Backward Compatibility

## Task
Migrate 114 records from old to new schema for IoT sensor data schema evolution
while maintaining **backward compatibility** for old-schema readers.

## Schema Changes

### Column Renames (require aliases):
  - `sid` → `sensor_id`
  - `t` → `epoch_ms`
  - `temp` → `temperature_c`

### Type Widenings (safe promotions):
  - `sensor_id`: → `int64`
  - `epoch_ms`: → `int64`

### New Nullable Columns:
  - `battery_pct` (float64, nullable)

## Backward Compatibility Rules
1. **Aliases**: write `aliases` metadata mapping new_name → old_name so old readers can find renamed columns
2. **Type widening**: only promote to wider types (int32→int64, float32→float64), never narrow
3. **Nullable columns**: new columns must be NULL/NaN (not 0/empty string)

## Data
- `data/old_data.csv`: source data in old schema
- `schema_old.json`: old schema definition
- `schema_new.json`: target schema with aliases

## Requirements
1. Load `data/old_data.csv`
2. Apply renames with aliases preserved in output metadata
3. Widen types to int64/float64 as specified
4. Add new nullable columns as None/NaN
5. Write migrated data to `data/migrated_data.csv`
6. Save to `results.json`:
   - `n_records`: row count
   - `columns`: list of column names in new schema
   - `aliases_written`: `true`
   - `types_widened`: `true`
   - `nullable_columns_null`: `true`
   - `dtypes`: dict of column → dtype string
7. Fix `migrate_schema.py`

## Deliverables
- Fixed `migrate_schema.py`
- `data/migrated_data.csv`
- `results.json`
