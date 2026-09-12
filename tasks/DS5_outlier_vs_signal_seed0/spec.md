# DS5: Outlier vs Signal

## Task
Apply correct outlier treatment to the **IoT sensor readings from manufacturing plant** dataset.
Dataset: `data/dataset.csv`

## Context
The anomaly detector identified 6 outlier groups. Each group requires a
DIFFERENT treatment. A blanket 'remove all outliers' strategy will FAIL —
it removes genuine signal groups and eliminates the ambiguous group that
must be flagged for human review.

## Outlier Group Classification

### Group 1: `startup_spike` (46 rows) — KEEP
**Description**: machine startup transients — genuine operational events (first 30s after power-on)
**Treatment**: **KEEP**
**Rationale**: Startup spikes are real physical events documented in the machine operating manual. Removing them would eliminate all startup sequences from the dataset, biasing the model toward steady-state operation only.

### Group 2: `sensor_fault` (33 rows) — REMOVE
**Description**: faulty sensor producing physically impossible negative readings
**Treatment**: **REMOVE**
**Rationale**: Negative sensor readings are physically impossible (sensor measures positive-only quantities). These are hardware fault artifacts confirmed by the maintenance log.

### Group 3: `furnace_ignition` (51 rows) — KEEP
**Description**: furnace ignition events — temperature spikes are genuine process events
**Treatment**: **KEEP**
**Rationale**: Furnace ignition is a documented process step. The detector threshold (500-900) is too aggressive and clips the upper tail of genuine ignition events (900-950°C). The correct threshold is 580-980.

**THRESHOLD BUG**: The current detector threshold for this group is
`500` to `900` — too aggressive.
The correct threshold is `580` to
`980`. Rows with `outlier_group == 'furnace_ignition'`
and `sensor_reading` outside the correct range should be reviewed.
For this task, treat ALL rows labeled `furnace_ignition` as KEEP (the label
reflects the corrected threshold).

### Group 4: `test_injection` (32 rows) — REMOVE
**Description**: synthetic test signals injected during calibration runs (value exactly = 0.00 or 9999.00)
**Treatment**: **REMOVE**
**Rationale**: Calibration test injections are documented in the QA log. They are not real machine readings and must be excluded from training data.

### Group 5: `overload_event` (35 rows) — KEEP
**Description**: overload protection events — genuine failure precursors with high predictive value
**Treatment**: **KEEP**
**Rationale**: Overload events are the primary failure precursors this model must learn to detect. Removing them from training data would eliminate the most informative examples of the target outcome.

### Group 6: `ambient_interference` (42 rows) — FLAG (do NOT remove)
**Description**: readings during scheduled nearby equipment operation — ambiguous origin
**Treatment**: **FLAG**
**Rationale**: Ambient interference readings could be genuine machine anomalies or artifacts from nearby equipment scheduled runs. Domain experts disagree on classification. Spec decision: create binary indicator column `ambient_flag` (1=ambiguous) and KEEP the rows. Do NOT remove them.

**Action**: Add column `ambient_flag` = 1 for all rows in this
group, then KEEP them in the output. Do NOT remove them.

## Treatment Summary

| Group | Label | Count | Treatment |
|-------|-------|-------|-----------|
| 1 | `startup_spike` | 46 | KEEP |
| normal | normal | 1998 | KEEP |
| 2 | `sensor_fault` | 33 | REMOVE |
| normal | normal | 1998 | KEEP |
| 3 | `furnace_ignition` | 51 | KEEP |
| normal | normal | 1998 | KEEP |
| 4 | `test_injection` | 32 | REMOVE |
| normal | normal | 1998 | KEEP |
| 5 | `overload_event` | 35 | KEEP |
| normal | normal | 1998 | KEEP |
| 6 | `ambient_interference` | 42 | FLAG + KEEP (add indicator column) |
| normal | normal | 1998 | KEEP |

## Requirements
1. **KEEP** rows where `outlier_group` is `1` (`startup_spike`), `3` (`furnace_ignition`), `5` (`overload_event`)
2. **REMOVE** rows where `outlier_group` is `2` (`sensor_fault`), `4` (`test_injection`)
3. **FLAG** rows where `outlier_group` is `6` (`ambient_interference`): add column `ambient_flag` = 1, keep in output
4. For all other rows: set `ambient_flag` = 0
5. Save cleaned dataset to `data/cleaned.csv` (expected: ~2172 rows)
6. Save stats to `cleaning_stats.json` with keys:
   - `cleaned_rows`, `removed_rows`
   - `group_1_kept`, `group_3_kept`, `group_5_kept` (must be > 0)
   - `group_2_removed`, `group_4_removed` (must equal original counts)
   - `ambient_flag_flagged` (must equal count of group 6 rows)
7. Script: `clean.py`

## Grading Note
The grader checks BOTH under-fixing AND over-fixing:
- Signal groups (1, 3, 5) present in cleaned output: +2 pts each
- Error groups (2, 4) absent from cleaned output: +2 pts each
- Group 6 present AND `ambient_flag` column created: +3 pts
- **Group 6 absent from cleaned output: -3 pts** (over-removal)
- Signal groups absent: -2 pts each (over-removal)

## Deliverables
- Fixed `clean.py`
- `data/cleaned.csv` with ~2172 rows and `ambient_flag` column
- `cleaning_stats.json`