#!/usr/bin/env bash
# Seed-aware grader for SPEC4: Database Schema Migration (Hard)
# Reads expected values from expected.json.
#
# Args: $1=WORKSPACE $2=REPORTS $3=SUBMISSION $4=TASK_DIR [$5=EXPECTED_JSON]
set -o pipefail
WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"
EXPECTED="${5:-$REPORTS/expected.json}"

mkdir -p "$REPORTS"

CHECKS=0; PASSED=0; FAILURES=""
check() {
  CHECKS=$((CHECKS + 1))
  if eval "$1" 2>/dev/null; then
    PASSED=$((PASSED + 1))
  else
    FAILURES="${FAILURES:+${FAILURES},}$2"
  fi
}

cd "$WORKSPACE"

# ── Check 1: Migration script runs without error ───────────────────────────
check "python3 migration.py" "migration_crash"

# ── Check 2: Database file still exists after migration ────────────────────
check "test -f database.db" "missing_database"

if [ -f "database.db" ] && [ -f "$EXPECTED" ]; then

# ── Check 3: v2 columns present, old columns gone ─────────────────────────
check "python3 -c \"
import sqlite3, json
expected = json.load(open('$EXPECTED'))
table = expected['table']
conn = sqlite3.connect('database.db')
cur = conn.cursor()
cur.execute(f'PRAGMA table_info({table})')
cols = [row[1] for row in cur.fetchall()]
conn.close()
for c in expected['v2_columns']:
    assert c in cols, f'Expected v2 column {c!r} not found in {cols}'
for c in expected['old_columns']:
    assert c not in cols, f'Old column {c!r} still present after migration'
print('COLUMNS_OK')
\"" "wrong_columns"

# ── Check 4: Row count unchanged ───────────────────────────────────────────
check "python3 -c \"
import sqlite3, json
expected = json.load(open('$EXPECTED'))
table = expected['table']
conn = sqlite3.connect('database.db')
cur = conn.cursor()
cur.execute(f'SELECT COUNT(*) FROM {table}')
count = cur.fetchone()[0]
conn.close()
assert count == expected['row_count'], f'Row count: expected {expected[\"row_count\"]}, got {count}'
print('ROW_COUNT_OK')
\"" "wrong_row_count"

# ── Check 5: Data preserved (spot-check by id, new column names) ──────────
check "python3 -c \"
import sqlite3, json
expected = json.load(open('$EXPECTED'))
table    = expected['table']
renames  = expected['renames']          # {old: new}
spot     = expected['spot_checks']      # {str(id): {...}}
keys     = list(renames.keys())
new_label   = renames[keys[0]]
new_contact = renames[keys[1]]
new_state   = renames[keys[2]]
new_value   = renames[keys[3]]
conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
for sid, vals in spot.items():
    cur.execute(f'SELECT * FROM {table} WHERE id=?', (int(sid),))
    row = cur.fetchone()
    assert row is not None, f'Row id={sid} missing after migration'
    assert str(row[new_label])   == str(vals['label_val']),   f'id={sid} {new_label}={row[new_label]!r} != {vals[\"label_val\"]!r}'
    assert str(row[new_contact]) == str(vals['contact_val']), f'id={sid} {new_contact}={row[new_contact]!r} != {vals[\"contact_val\"]!r}'
    assert str(row[new_state])   == str(vals['state_val']),   f'id={sid} {new_state}={row[new_state]!r} != {vals[\"state_val\"]!r}'
    assert str(row['ref_id'])    == str(vals['ref_id']),      f'id={sid} ref_id={row[\"ref_id\"]!r} != {vals[\"ref_id\"]!r}'
conn.close()
print('DATA_PRESERVED_OK')
\"" "data_not_preserved"

# ── Check 6: No data loss — all original IDs present ──────────────────────
check "python3 -c \"
import sqlite3, json
expected = json.load(open('$EXPECTED'))
table = expected['table']
spot  = expected['spot_checks']
conn  = sqlite3.connect('database.db')
cur   = conn.cursor()
cur.execute(f'SELECT id FROM {table}')
ids_in_db = {str(row[0]) for row in cur.fetchall()}
conn.close()
for sid in spot.keys():
    assert sid in ids_in_db, f'id={sid} lost after migration'
print('NO_DATA_LOSS_OK')
\"" "data_loss"

# ── Check 7: New columns added with correct default values ─────────────────
check "python3 -c \"
import sqlite3, json
expected = json.load(open('$EXPECTED'))
table    = expected['table']
defaults = expected['new_columns_defaults']
conn     = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
cur      = conn.cursor()
cur.execute(f'PRAGMA table_info({table})')
col_names = [row[1] for row in cur.fetchall()]
for col in expected['new_columns_added']:
    assert col in col_names, f'New column {col!r} not found'
cur.execute(f'SELECT * FROM {table} LIMIT 5')
rows = cur.fetchall()
for row in rows:
    for col, dflt in defaults.items():
        val = row[col]
        assert str(val) == str(dflt), f'Column {col}: expected default {dflt!r}, got {val!r}'
conn.close()
print('NEW_COLUMNS_OK')
\"" "new_columns_wrong"

# ── Check 8: Value column type change correct ─────────────────────────────
check "python3 -c \"
import sqlite3, json
expected  = json.load(open('$EXPECTED'))
table     = expected['table']
tc        = expected['value_col_type_change']
new_col   = tc['col']
new_type  = tc['new_type']
conn      = sqlite3.connect('database.db')
cur       = conn.cursor()
cur.execute(f'PRAGMA table_info({table})')
col_info  = {row[1]: row[2].upper() for row in cur.fetchall()}
conn.close()
assert new_col in col_info, f'Column {new_col!r} not found'
assert new_type.upper() in col_info[new_col], f'Type mismatch: {new_col} is {col_info[new_col]}, expected {new_type}'
print('TYPE_CHANGE_OK')
\"" "type_change_wrong"

# ── Check 9: Indexes created (including unique index on contact col) ───────
check "python3 -c \"
import sqlite3, json
expected = json.load(open('$EXPECTED'))
table    = expected['table']
renames  = expected['renames']
keys     = list(renames.keys())
new_contact = renames[keys[1]]
conn = sqlite3.connect('database.db')
cur  = conn.cursor()
cur.execute(f'PRAGMA index_list({table})')
indexes = cur.fetchall()
found_unique = False
for idx in indexes:
    idx_name = idx[1]
    is_unique = idx[2]
    cur.execute(f'PRAGMA index_info({idx_name})')
    idx_cols = [r[2] for r in cur.fetchall()]
    if new_contact in idx_cols and is_unique:
        found_unique = True
        break
conn.close()
assert found_unique, f'No unique index found on {new_contact}'
print('UNIQUE_INDEX_OK')
\"" "no_unique_index"

# ── Check 10: FK present in schema (via table SQL or PRAGMA) ──────────────
check "python3 -c \"
import sqlite3, json
expected  = json.load(open('$EXPECTED'))
table     = expected['table']
ref_table = expected['ref_table']
conn      = sqlite3.connect('database.db')
cur       = conn.cursor()
cur.execute(f'PRAGMA foreign_key_list({table})')
fks = cur.fetchall()
# Also check sqlite_master for REFERENCES keyword as fallback
cur.execute(\"SELECT sql FROM sqlite_master WHERE type='table' AND name=?\", (table,))
tbl_sql = (cur.fetchone() or [''])[0] or ''
conn.close()
fk_found = any(str(fk[2]).lower() == ref_table.lower() for fk in fks)
ref_in_sql = ref_table.lower() in tbl_sql.lower() or 'references' in tbl_sql.lower()
assert fk_found or ref_in_sql, f'FK to {ref_table} not found in schema (fks={fks})'
print('FK_OK')
\"" "fk_missing"

# ── Check 11: Schema matches v2 exactly (column set) ──────────────────────
check "python3 -c \"
import sqlite3, json
expected = json.load(open('$EXPECTED'))
table    = expected['table']
conn     = sqlite3.connect('database.db')
cur      = conn.cursor()
cur.execute(f'PRAGMA table_info({table})')
cols     = [row[1] for row in cur.fetchall()]
conn.close()
v2_set   = set(expected['v2_columns'])
db_set   = set(cols)
extra    = db_set - v2_set
missing  = v2_set - db_set
assert not extra,   f'Unexpected columns present: {extra}'
assert not missing, f'Expected columns missing: {missing}'
print('SCHEMA_V2_OK')
\"" "schema_v2_mismatch"

# ── Check 12: Idempotent — second run must not crash ──────────────────────
check "python3 migration.py" "not_idempotent"

fi

# ── Check 13: Attestation file produced ───────────────────────────────────
check "python3 -c \"
import json, os
for path in ['migration_result.json', '$SUBMISSION/migration_result.json', '$REPORTS/migration_result.json']:
    if os.path.exists(path):
        att = json.load(open(path))
        assert att.get('verdict') == 'pass', f'verdict={att.get(\"verdict\")!r}'
        print('ATTESTATION_OK')
        raise SystemExit(0)
raise AssertionError('migration_result.json not found')
\"" "bad_attestation"

# ── Score ──────────────────────────────────────────────────────────────────
PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
    SUCCESS=1; PASS=true
else
    SUCCESS=0; PASS=false
fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {
    "checks_passed": $PASSED,
    "checks_total": $CHECKS,
    "partial_score": $PARTIAL
  },
  "failure_modes": $FM
}
JSON
