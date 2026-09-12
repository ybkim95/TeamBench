# DS28: Timestamp Timezone Reconciliation

## Task
Reconcile **67 records** from three sources with different timestamp conventions
for IoT sensor timestamp reconciliation. All timestamps must be converted to UTC Unix seconds.

## Source Conventions

| Source | Format | Convention |
|--------|--------|------------|
| `cloud_gateway` | `unix_ts` (integer) | UTC Unix timestamp — no conversion needed |
| `local_controller` | `local_time` (integer stored as unix) + `timezone` column | Local time in `Europe/Berlin` with DST |
| `embedded_firmware` | `custom_ts` (integer) | Seconds since **GPS epoch (1980-01-06)** (offset=315532800) |

## Conversion Rules
1. **Source A**: `utc_ts = unix_ts` (already UTC)
2. **Source B**: Use `pytz.timezone("Europe/Berlin")` for DST-aware localization
   - The `local_time` column stores Unix timestamps; the `timezone` column names the source TZ
   - Convert: `pd.to_datetime(local_time, unit='s').dt.tz_localize('Europe/Berlin').dt.tz_convert('UTC')`
3. **Source C**: `utc_ts = custom_ts + 315532800`
   - **GPS epoch (1980-01-06)** = 315532800 seconds after Unix epoch

## Data
- `data/cloud_gateway.csv`: id, unix_ts, measurement
- `data/local_controller.csv`: id, local_time, timezone, measurement
- `data/embedded_firmware.csv`: id, custom_ts, measurement

## Requirements
1. Load all three sources
2. Apply correct timestamp conversions
3. Combine into unified DataFrame with columns: id, utc_ts, measurement, source
4. Write to `data/reconciled.csv`
5. Save to `results.json`:
   - `total_records`: 201
   - `sources`: list of source names
   - `epoch_c_offset_used`: 315532800 (correct value)
   - `tz_b_dst_aware`: `true`
   - `reconciliation_correct`: `true`
6. Fix `reconcile_timestamps.py`

## Deliverables
- Fixed `reconcile_timestamps.py`
- `data/reconciled.csv`
- `results.json`
