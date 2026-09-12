# DS28: Timestamp Timezone Reconciliation

## Task
Reconcile **99 records** from three sources with different timestamp conventions
for financial trade timestamp reconciliation. All timestamps must be converted to UTC Unix seconds.

## Source Conventions

| Source | Format | Convention |
|--------|--------|------------|
| `exchange_feed` | `unix_ts` (integer) | UTC Unix timestamp — no conversion needed |
| `broker_system` | `local_time` (integer stored as unix) + `timezone` column | Local time in `US/Eastern` with DST |
| `clearing_house` | `custom_ts` (integer) | Seconds since **Y2K epoch (2000-01-01)** (offset=946684800) |

## Conversion Rules
1. **Source A**: `utc_ts = unix_ts` (already UTC)
2. **Source B**: Use `pytz.timezone("US/Eastern")` for DST-aware localization
   - The `local_time` column stores Unix timestamps; the `timezone` column names the source TZ
   - Convert: `pd.to_datetime(local_time, unit='s').dt.tz_localize('US/Eastern').dt.tz_convert('UTC')`
3. **Source C**: `utc_ts = custom_ts + 946684800`
   - **Y2K epoch (2000-01-01)** = 946684800 seconds after Unix epoch

## Data
- `data/exchange_feed.csv`: id, unix_ts, price
- `data/broker_system.csv`: id, local_time, timezone, price
- `data/clearing_house.csv`: id, custom_ts, price

## Requirements
1. Load all three sources
2. Apply correct timestamp conversions
3. Combine into unified DataFrame with columns: id, utc_ts, price, source
4. Write to `data/reconciled.csv`
5. Save to `results.json`:
   - `total_records`: 297
   - `sources`: list of source names
   - `epoch_c_offset_used`: 946684800 (correct value)
   - `tz_b_dst_aware`: `true`
   - `reconciliation_correct`: `true`
6. Fix `reconcile_timestamps.py`

## Deliverables
- Fixed `reconcile_timestamps.py`
- `data/reconciled.csv`
- `results.json`
