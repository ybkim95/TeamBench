# DS5: Outlier vs Signal

## Task
Apply correct outlier treatment to the **network packet capture anomaly dataset** dataset.
Dataset: `data/dataset.csv`

## Context
The anomaly detector identified 6 outlier groups. Each group requires a
DIFFERENT treatment. A blanket 'remove all outliers' strategy will FAIL —
it removes genuine signal groups and eliminates the ambiguous group that
must be flagged for human review.

## Outlier Group Classification

### Group 1: `jumbo_frame` (38 rows) — KEEP
**Description**: jumbo Ethernet frames (9000 bytes) — legitimate large-payload transfers
**Treatment**: **KEEP**
**Rationale**: Jumbo frames are standard for high-throughput storage and backup traffic. The network is configured for jumbo frame support (MTU 9000). These are expected legitimate traffic.

### Group 2: `malformed_packet` (31 rows) — REMOVE
**Description**: malformed packets with size < 14 bytes (below Ethernet minimum frame size)
**Treatment**: **REMOVE**
**Rationale**: Packets below 14 bytes are smaller than the minimum Ethernet frame size including headers. These are driver-level artifacts and physically invalid captures.

### Group 3: `ddos_amplification` (61 rows) — KEEP
**Description**: DDoS amplification attack traffic — high-value attack signal
**Treatment**: **KEEP**
**Rationale**: DDoS amplification packets are confirmed attack traffic (SOC alert #2024-1147). The detector upper threshold (55000) clips legitimate amplification payloads that can reach the Ethernet MTU limit (65535). The correct upper bound is 65535.

**THRESHOLD BUG**: The current detector threshold for this group is
`3000` to `55000` — too aggressive.
The correct threshold is `3500` to
`65535`. Rows with `outlier_group == 'ddos_amplification'`
and `packet_size_bytes` outside the correct range should be reviewed.
For this task, treat ALL rows labeled `ddos_amplification` as KEEP (the label
reflects the corrected threshold).

### Group 4: `test_probe` (25 rows) — REMOVE
**Description**: synthetic test probes injected by the monitoring system every 60s
**Treatment**: **REMOVE**
**Rationale**: 42-byte probes are injected by the network monitoring system at 60-second intervals (documented in NOC procedures). They are synthetic and must not appear in anomaly training data.

### Group 5: `exfiltration_burst` (44 rows) — KEEP
**Description**: confirmed data exfiltration bursts — primary attack signal for intrusion detection
**Treatment**: **KEEP**
**Rationale**: Confirmed exfiltration bursts are the primary anomaly class this model must detect. Removing them from training data eliminates the most important positive-class examples.

### Group 6: `encrypted_unknown` (45 rows) — FLAG (do NOT remove)
**Description**: encrypted traffic with unknown certificates — ambiguous (legitimate or C2)
**Treatment**: **FLAG**
**Rationale**: Encrypted traffic with unknown/self-signed certificates could be legitimate (IoT devices, internal tools) or command-and-control communication. Threat intelligence has not conclusively classified these. Spec decision: create binary indicator `tls_unknown_flag` (1=unknown cert) and KEEP rows for analyst review.

**Action**: Add column `tls_unknown_flag` = 1 for all rows in this
group, then KEEP them in the output. Do NOT remove them.

## Treatment Summary

| Group | Label | Count | Treatment |
|-------|-------|-------|-----------|
| 1 | `jumbo_frame` | 38 | KEEP |
| normal | normal | 2114 | KEEP |
| 2 | `malformed_packet` | 31 | REMOVE |
| normal | normal | 2114 | KEEP |
| 3 | `ddos_amplification` | 61 | KEEP |
| normal | normal | 2114 | KEEP |
| 4 | `test_probe` | 25 | REMOVE |
| normal | normal | 2114 | KEEP |
| 5 | `exfiltration_burst` | 44 | KEEP |
| normal | normal | 2114 | KEEP |
| 6 | `encrypted_unknown` | 45 | FLAG + KEEP (add indicator column) |
| normal | normal | 2114 | KEEP |

## Requirements
1. **KEEP** rows where `outlier_group` is `1` (`jumbo_frame`), `3` (`ddos_amplification`), `5` (`exfiltration_burst`)
2. **REMOVE** rows where `outlier_group` is `2` (`malformed_packet`), `4` (`test_probe`)
3. **FLAG** rows where `outlier_group` is `6` (`encrypted_unknown`): add column `tls_unknown_flag` = 1, keep in output
4. For all other rows: set `tls_unknown_flag` = 0
5. Save cleaned dataset to `data/cleaned.csv` (expected: ~2302 rows)
6. Save stats to `cleaning_stats.json` with keys:
   - `cleaned_rows`, `removed_rows`
   - `group_1_kept`, `group_3_kept`, `group_5_kept` (must be > 0)
   - `group_2_removed`, `group_4_removed` (must equal original counts)
   - `tls_unknown_flag_flagged` (must equal count of group 6 rows)
7. Script: `clean.py`

## Grading Note
The grader checks BOTH under-fixing AND over-fixing:
- Signal groups (1, 3, 5) present in cleaned output: +2 pts each
- Error groups (2, 4) absent from cleaned output: +2 pts each
- Group 6 present AND `tls_unknown_flag` column created: +3 pts
- **Group 6 absent from cleaned output: -3 pts** (over-removal)
- Signal groups absent: -2 pts each (over-removal)

## Deliverables
- Fixed `clean.py`
- `data/cleaned.csv` with ~2302 rows and `tls_unknown_flag` column
- `cleaning_stats.json`