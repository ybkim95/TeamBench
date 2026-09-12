# D6: Data Reconciliation — Full Specification

## Context
Subscriber records across identity and subscription-management systems.  Two system snapshots have drifted out of sync.
System A (`Identity`) and System B (`SubscriptionMgr`) each hold overlapping
records with approximately 32 distinct entities across both systems.

## Field Ownership (Source-of-Truth Designation)

### System A (`Identity`) is authoritative for:
  - `username`
  - `email`
  - `display_name`
  - `auth_provider`

### System B (`SubscriptionMgr`) is authoritative for:
  - `plan_id`
  - `renewal_date`
  - `seats`
  - `discount_pct`

### Shared fields (conflict resolved by timestamp):
  - `account_status`
  - `timezone`

## Conflict Resolution Rules — in strict priority order

1. **Manual Override** (highest priority):
   If a System B record has `"manual_override": true`, System B's values win for
   **ALL** fields of that record — including fields normally owned by System A.
   `reconcile_source` must be set to `"manual_override"`.

2. **Field Ownership**:
   - A-owned fields: always take the value from System A, regardless of timestamps.
   - B-owned fields: always take the value from System B, regardless of timestamps.

3. **Shared Field Conflict Resolution**:
   For shared fields where System A and System B have different values:
   - Compare `last_updated` timestamps (ISO 8601 strings).
   - The record from the system with the **newer** (larger) timestamp wins for
     all shared fields of that record pair.
   - If timestamps are equal, System A takes precedence.

4. **Records only in System A**:
   Include the record. Fill all B-owned fields with `null`.
   `reconcile_source` = `"system_a_only"`.

5. **Records only in System B**:
   Include the record. Fill all A-owned fields with `null`.
   `reconcile_source` = `"system_b_only"`.

6. **Records present in both systems with no conflicts**:
   Merge normally following field-ownership rules.
   `reconcile_source` = `"merged"`.

## Output Format

### File: `reconciled.json`
A JSON array of objects, **sorted ascending by `subscriber_id`**.

Each object must contain exactly these fields in order:
`subscriber_id`, `username`, `email`, `display_name`, `auth_provider`, `plan_id`, `renewal_date`, `seats`, `discount_pct`, `account_status`, `timezone`, `reconcile_source`

- `reconcile_source` must be one of: `"merged"`, `"manual_override"`,
  `"system_a_only"`, `"system_b_only"`.
- Fields that have no source (null-filled) must appear as JSON `null`, not
  omitted and not the string `"null"`.
- No extra fields. No missing fields.

## Execution
```
python reconcile.py
```
Reads `system_a.json` and `system_b.json` from the current directory,
writes `reconciled.json` to the current directory.

## Deliverables
- Fixed `reconcile.py` in workspace.
- `reconciled.json` present and correct.
- Verifier attests all rules are satisfied.
