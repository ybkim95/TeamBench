#!/usr/bin/env bash
# Seed-aware grader for D3: Database Schema Migration
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

# ── Check 3: v2 columns exist (old columns gone, new columns present) ──────
check "python3 -c \"
import sqlite3, json
expected = json.load(open('$EXPECTED'))
table = expected['table']
conn = sqlite3.connect('database.db')
cur = conn.cursor()
cur.execute(f'PRAGMA table_info({table})')
cols = [row[1] for row in cur.fetchall()]
conn.close()
v2 = expected['v2_columns']
for c in v2:
    assert c in cols, f'Expected column {c!r} not found in {cols}'
old = expected['old_columns']
for c in old:
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

# ── Check 5: Old data preserved (spot-check by id) ────────────────────────
check "python3 -c \"
import sqlite3, json
expected = json.load(open('$EXPECTED'))
table = expected['table']
renames = expected['renames']          # {old: new}
spot = expected['spot_checks']         # {str(id): {old_name_val, ...}}
old_to_new = renames                   # maps old col name -> new col name
new_name   = old_to_new[list(old_to_new)[0]]
new_email  = old_to_new[list(old_to_new)[1]]
new_status = old_to_new[list(old_to_new)[2]]
new_amount = old_to_new[list(old_to_new)[3]]
conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
for sid, vals in spot.items():
    cur.execute(f'SELECT * FROM {table} WHERE id=?', (int(sid),))
    row = cur.fetchone()
    assert row is not None, f'Row id={sid} missing after migration'
    assert row[new_name]   == vals['old_name_val'],   f'id={sid} {new_name}={row[new_name]!r} != {vals[\"old_name_val\"]!r}'
    assert row[new_email]  == vals['old_email_val'],  f'id={sid} {new_email}={row[new_email]!r} != {vals[\"old_email_val\"]!r}'
    assert row[new_status] == vals['old_status_val'], f'id={sid} {new_status}={row[new_status]!r} != {vals[\"old_status_val\"]!r}'
    assert row[new_amount] == vals['old_amount_val'], f'id={sid} {new_amount}={row[new_amount]!r} != {vals[\"old_amount_val\"]!r}'
conn.close()
print('DATA_PRESERVED_OK')
\"" "data_not_preserved"

# ── Check 6: Column renames applied (no old column names remain) ───────────
check "python3 -c \"
import sqlite3, json
expected = json.load(open('$EXPECTED'))
table = expected['table']
conn = sqlite3.connect('database.db')
cur = conn.cursor()
cur.execute(f'PRAGMA table_info({table})')
cols = [row[1] for row in cur.fetchall()]
conn.close()
for old_col in expected['old_columns']:
    assert old_col not in cols, f'Old column {old_col!r} still present'
print('RENAMES_OK')
\"" "renames_not_applied"

# ── Check 7: New columns added with correct defaults ───────────────────────
check "python3 -c \"
import sqlite3, json
expected = json.load(open('$EXPECTED'))
table = expected['table']
defaults = expected['new_columns_defaults']
conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute(f'PRAGMA table_info({table})')
col_info = {row[1]: row[4] for row in cur.fetchall()}  # name -> dflt_value
added = expected['new_columns_added']
for col in added:
    assert col in col_info, f'New column {col!r} not found'
# Check actual row values equal the default (all rows were inserted before migration)
cur.execute(f'SELECT * FROM {table} LIMIT 3')
rows = cur.fetchall()
for row in rows:
    for col, dflt in defaults.items():
        val = row[col]
        # Compare as string for flexibility (INTEGER default '0' == int 0)
        assert str(val) == str(dflt), f'Column {col}: expected default {dflt!r}, got {val!r}'
conn.close()
print('NEW_COLUMNS_OK')
\"" "new_columns_wrong"

# ── Check 8: No data loss — all original IDs present ──────────────────────
check "python3 -c \"
import sqlite3, json
expected = json.load(open('$EXPECTED'))
table = expected['table']
spot = expected['spot_checks']
conn = sqlite3.connect('database.db')
cur = conn.cursor()
cur.execute(f'SELECT id FROM {table}')
ids_in_db = {str(row[0]) for row in cur.fetchall()}
conn.close()
for sid in spot.keys():
    assert sid in ids_in_db, f'id={sid} lost after migration'
print('NO_DATA_LOSS_OK')
\"" "data_loss"

# ── Check 9: Schema matches v2 exactly (column set) ───────────────────────
check "python3 -c \"
import sqlite3, json
expected = json.load(open('$EXPECTED'))
table = expected['table']
conn = sqlite3.connect('database.db')
cur = conn.cursor()
cur.execute(f'PRAGMA table_info({table})')
cols = [row[1] for row in cur.fetchall()]
conn.close()
v2_set = set(expected['v2_columns'])
db_set  = set(cols)
extra   = db_set - v2_set
missing = v2_set - db_set
assert not extra,   f'Unexpected columns present: {extra}'
assert not missing, f'Expected columns missing: {missing}'
print('SCHEMA_V2_OK')
\"" "schema_v2_mismatch"

# ── Check 10: Unique index on email column ─────────────────────────────────
check "python3 -c \"
import sqlite3, json
expected = json.load(open('$EXPECTED'))
table = expected['table']
renames = expected['renames']
new_email = list(renames.values())[1]   # second rename entry is email
conn = sqlite3.connect('database.db')
cur = conn.cursor()
cur.execute(f'PRAGMA index_list({table})')
indexes = cur.fetchall()
found_unique = False
for idx in indexes:
    idx_name = idx[1]
    is_unique = idx[2]
    cur.execute(f'PRAGMA index_info({idx_name})')
    idx_cols = [r[2] for r in cur.fetchall()]
    if new_email in idx_cols and is_unique:
        found_unique = True
        break
conn.close()
assert found_unique, f'No unique index found on {new_email}'
print('UNIQUE_INDEX_OK')
\"" "no_unique_index"

fi

# ── Check 10 (attestation): Verifier produced attestation ─────────────────
check "python3 -c \"
import json, sys
att_path = '$SUBMISSION/attestation.json'
try:
    att = json.load(open(att_path))
except FileNotFoundError:
    # Also accept attestation inside workspace
    att = json.load(open('migration_result.json'))
assert att.get('verdict') == 'pass', f'Attestation verdict={att.get(\"verdict\")!r}'
\" 2>/dev/null || python3 -c \"
import json
att = json.load(open('migration_result.json'))
assert att.get('verdict') == 'pass'
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
