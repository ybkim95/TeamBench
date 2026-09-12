#!/usr/bin/env bash
# DB1_migration_conflict grader — apply migrations to SQLite and verify schema.
# Checks: no duplicate sequence numbers, correct column renames, analytics table,
# correct FK references, and expected index.
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

mkdir -p "${REPORTS}"

pass=true
partial=0
total=10
findings=""

check() {
    local id="$1"
    local desc="$2"
    local result="$3"
    if [ "$result" = "pass" ]; then
        partial=$((partial + 1))
        findings="${findings}{\"id\":\"${id}\",\"ok\":true,\"note\":\"${desc}\"},"
    else
        pass=false
        findings="${findings}{\"id\":\"${id}\",\"ok\":false,\"note\":\"${desc}\"},"
    fi
}

# ── Load expected values ───────────────────────────────────────────────────────
EXPECTED_JSON="${REPORTS}/expected.json"
if [ ! -f "${EXPECTED_JSON}" ]; then
    EXPECTED_JSON="${TASK_DIR}/expected.json"
fi

PRIMARY_TABLE=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('primary_table', 'orders'))
" 2>/dev/null || echo "orders")

SECONDARY_TABLE=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('secondary_table', 'customers'))
" 2>/dev/null || echo "customers")

ANALYTICS_TABLE=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(e.get('analytics_table', 'order_metrics'))
" 2>/dev/null || echo "order_metrics")

# Get expected column names from expected.json
EXPECTED_NEW_COL=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
cols = e.get('expected_secondary_cols', [])
# new_col is not 'id', 'email', 'created_at'
for c in cols:
    if c not in ('id', 'email', 'created_at', 'joined_at'):
        print(c)
        break
" 2>/dev/null || echo "full_name")

CONFLICTS=$(python3 -c "
import json
e = json.load(open('${EXPECTED_JSON}'))
print(' '.join(e.get('conflicts', [])))
" 2>/dev/null || echo "")

MIGRATIONS_DIR="${WORKSPACE}/migrations"
DB_PATH="${REPORTS}/schema_test.db"

# ── C1: migrations/ directory exists ──────────────────────────────────────────
check "C1" "migrations/ directory exists" "$([ -d '${MIGRATIONS_DIR}' ] && echo pass || echo fail)"

# ── C2: No duplicate sequence numbers ─────────────────────────────────────────
result=$(python3 -c "
import os, glob
mdir = '${MIGRATIONS_DIR}'
if not os.path.isdir(mdir):
    print('fail')
    raise SystemExit
files = glob.glob(os.path.join(mdir, '*.sql'))
seq_nums = [os.path.basename(f).split('_')[0] for f in files]
dupes = [s for s in seq_nums if seq_nums.count(s) > 1]
print('fail' if dupes else 'pass')
" 2>/dev/null || echo "fail")
check "C2" "No duplicate sequence numbers in migrations/" "${result}"

# ── C3: Migrations apply cleanly to SQLite ────────────────────────────────────
result=$(python3 -c "
import sqlite3, os, glob, sys

db = '${DB_PATH}'
mdir = '${MIGRATIONS_DIR}'

if os.path.exists(db):
    os.remove(db)

files = sorted(glob.glob(os.path.join(mdir, '*.sql')))
if not files:
    print('fail')
    raise SystemExit

try:
    conn = sqlite3.connect(db)
    conn.execute('PRAGMA foreign_keys = ON')
    for f in files:
        sql = open(f).read()
        conn.executescript(sql)
    conn.commit()
    conn.close()
    print('pass')
except Exception as e:
    print('fail')
" 2>/dev/null || echo "fail")
check "C3" "All migrations apply to SQLite without errors" "${result}"

# ── C4: Secondary table has new column (renamed) ──────────────────────────────
result=$(python3 -c "
import sqlite3, os

db = '${DB_PATH}'
if not os.path.exists(db):
    print('fail')
    raise SystemExit

conn = sqlite3.connect(db)
rows = conn.execute('PRAGMA table_info(${SECONDARY_TABLE})').fetchall()
cols = [r[1] for r in rows]
conn.close()
new_col = '${EXPECTED_NEW_COL}'
print('pass' if new_col in cols else 'fail')
" 2>/dev/null || echo "fail")
check "C4" "${SECONDARY_TABLE} has renamed column ${EXPECTED_NEW_COL}" "${result}"

# ── C5: Secondary table does NOT have old column name ─────────────────────────
result=$(python3 -c "
import sqlite3, os, json

db = '${DB_PATH}'
if not os.path.exists(db):
    print('fail')
    raise SystemExit

e = json.load(open('${EXPECTED_JSON}'))
# Find old_col: it's in expected_secondary_cols of seed=0 if not renamed,
# but we need the ORIGINAL old col. Derive from domain data.
domain = e.get('domain', 'ecommerce')
old_cols = {
    'ecommerce': 'customer_name', 'social': 'display_name',
    'analytics': 'source_name', 'inventory': 'warehouse_name',
    'billing': 'account_name',
}
old_col = old_cols.get(domain, 'customer_name')

conn = sqlite3.connect(db)
rows = conn.execute('PRAGMA table_info(${SECONDARY_TABLE})').fetchall()
cols = [r[1] for r in rows]
conn.close()
# Old column should be gone (renamed)
conflicts = '${CONFLICTS}'.split()
if 'column_rename_conflict' in conflicts:
    print('pass' if old_col not in cols else 'fail')
else:
    print('pass')
" 2>/dev/null || echo "pass")
check "C5" "${SECONDARY_TABLE} does NOT have old column name (rename complete)" "${result}"

# ── C6: Primary table has extra column ───────────────────────────────────────
result=$(python3 -c "
import sqlite3, os, json

db = '${DB_PATH}'
if not os.path.exists(db):
    print('fail')
    raise SystemExit

e = json.load(open('${EXPECTED_JSON}'))
domain = e.get('domain', 'ecommerce')
extra_cols = {
    'ecommerce': 'region', 'social': 'language',
    'analytics': 'environment', 'inventory': 'zone',
    'billing': 'currency',
}
extra_col = extra_cols.get(domain, 'region')

conn = sqlite3.connect(db)
rows = conn.execute('PRAGMA table_info(${PRIMARY_TABLE})').fetchall()
cols = [r[1] for r in rows]
conn.close()
print('pass' if extra_col in cols else 'fail')
" 2>/dev/null || echo "fail")
check "C6" "${PRIMARY_TABLE} has extra column added by branch A" "${result}"

# ── C7: Analytics table exists ────────────────────────────────────────────────
result=$(python3 -c "
import sqlite3, os

db = '${DB_PATH}'
if not os.path.exists(db):
    print('fail')
    raise SystemExit

conn = sqlite3.connect(db)
r = conn.execute(
    \"SELECT name FROM sqlite_master WHERE type='table' AND name=?\",
    ('${ANALYTICS_TABLE}',)
).fetchone()
conn.close()
print('pass' if r else 'fail')
" 2>/dev/null || echo "fail")
check "C7" "Analytics table ${ANALYTICS_TABLE} exists" "${result}"

# ── C8: Analytics table references new column (not old name) ─────────────────
result=$(python3 -c "
import sqlite3, os, json

db = '${DB_PATH}'
if not os.path.exists(db):
    print('fail')
    raise SystemExit

e = json.load(open('${EXPECTED_JSON}'))
domain = e.get('domain', 'ecommerce')
new_cols = {
    'ecommerce': 'full_name', 'social': 'username',
    'analytics': 'source_label', 'inventory': 'location_name',
    'billing': 'company_name',
}
old_cols = {
    'ecommerce': 'customer_name', 'social': 'display_name',
    'analytics': 'source_name', 'inventory': 'warehouse_name',
    'billing': 'account_name',
}
new_col = new_cols.get(domain, 'full_name')
old_col = old_cols.get(domain, 'customer_name')

try:
    conn = sqlite3.connect(db)
    rows = conn.execute('PRAGMA table_info(${ANALYTICS_TABLE})').fetchall()
    cols = [r[1] for r in rows]
    conn.close()
    conflicts = '${CONFLICTS}'.split()
    if 'column_rename_conflict' in conflicts:
        print('pass' if new_col in cols and old_col not in cols else 'fail')
    else:
        print('pass')
except Exception:
    print('fail')
" 2>/dev/null || echo "fail")
check "C8" "${ANALYTICS_TABLE} uses new column name (not old name)" "${result}"

# ── C9: Index exists ──────────────────────────────────────────────────────────
result=$(python3 -c "
import sqlite3, os, json

db = '${DB_PATH}'
if not os.path.exists(db):
    print('fail')
    raise SystemExit

e = json.load(open('${EXPECTED_JSON}'))
domain = e.get('domain', 'ecommerce')
index_names = {
    'ecommerce': 'idx_orders_customer', 'social': 'idx_posts_user',
    'analytics': 'idx_events_source', 'inventory': 'idx_items_warehouse',
    'billing': 'idx_invoices_account',
}
index_name = index_names.get(domain, 'idx_orders_customer')

conn = sqlite3.connect(db)
r = conn.execute(
    \"SELECT name FROM sqlite_master WHERE type='index' AND name=?\",
    (index_name,)
).fetchone()
conn.close()
conflicts = '${CONFLICTS}'.split()
if 'index_name_collision' in conflicts:
    print('pass' if r else 'fail')
else:
    print('pass')
" 2>/dev/null || echo "pass")
check "C9" "Expected index exists (no duplicate index names)" "${result}"

# ── C10: migration_policy.md present ──────────────────────────────────────────
check "C10" "migration_policy.md present in workspace" "$([ -f '${WORKSPACE}/migration_policy.md' ] && echo pass || echo fail)"

# ── Write score.json ──────────────────────────────────────────────────────────
partial_score=$(python3 -c "print(round(${partial} / ${total}, 2))")
findings="${findings%,}"

cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "${pass}" = "true" ] && echo "true" || echo "false" ),
  "primary": {"success": $( [ "${pass}" = "true" ] && echo 1 || echo 0 )},
  "secondary": {
    "partial_score": ${partial_score},
    "checks_passed": ${partial},
    "checks_total": ${total}
  },
  "failure_modes": [],
  "checklist": [${findings}]
}
EOF
