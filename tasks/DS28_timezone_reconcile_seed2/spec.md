# DS28: Timestamp Timezone Reconciliation

## Task
Reconcile **57 records** from three sources with different timestamp conventions
for logistics event timestamp reconciliation. All timestamps must be converted to UTC Unix seconds.

## Source Conventions

| Source | Format | Convention |
|--------|--------|------------|
| `central_hub` | `unix_ts` (integer) | UTC Unix timestamp — no conversion needed |
| `regional_depot` | `local_time` (integer stored as unix) + `timezone` column | Local time in `Asia/Tokyo` with DST |
| `rfid_scanner` | `custom_ts` (integer) | Seconds since **Custom epoch (2004-01-01)** (offset=1072915200) |

## Conversion Rules
1. **Source A**: `utc_ts = unix_ts` (already UTC)
2. **Source B**: Use `pytz.timezone("Asia/Tokyo")` for DST-aware localization
   - The `local_time` column stores Unix timestamps; the `timezone` column names the source TZ
   - Convert: `pd.to_datetime(local_time, unit='s').dt.tz_localize('Asia/Tokyo').dt.tz_convert('UTC')`
3. **Source C**: `utc_ts = custom_ts + 1072915200`
   - **Custom epoch (2004-01-01)** = 1072915200 seconds after Unix epoch

## Data
- `data/central_hub.csv`: id, unix_ts, weight_kg
- `data/regional_depot.csv`: id, local_time, timezone, weight_kg
- `data/rfid_scanner.csv`: id, custom_ts, weight_kg

## Requirements
1. Load all three sources
2. Apply correct timestamp conversions
3. Combine into unified DataFrame with columns: id, utc_ts, weight_kg, source
4. Write to `data/reconciled.csv`
5. Save to `results.json`:
   - `total_records`: 171
   - `sources`: list of source names
   - `epoch_c_offset_used`: 1072915200 (correct value)
   - `tz_b_dst_aware`: `true`
   - `reconciliation_correct`: `true`
6. Fix `reconcile_timestamps.py`

## Deliverables
- Fixed `reconcile_timestamps.py`
- `data/reconciled.csv`
- `results.json`
