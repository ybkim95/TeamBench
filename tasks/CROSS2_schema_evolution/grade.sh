#!/usr/bin/env bash
# CROSS2 grader: verify schema evolution — Service B updated + backfill implemented
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

cd "$WORKSPACE"

pass=true
partial=0
total=12
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

# Install pytest if needed
# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require pytest || true

# -------------------------------------------------------------------
# Detect seed-parameterised names from migration file
# -------------------------------------------------------------------
NEW_COL=$(python3 -c "
import re, sys
src = open('service_a/migrations/002_add_columns.py').read()
# Find the new table name for the primary entity column (renamed column)
# Look for INSERT ... SELECT pattern to find old->new name mapping
m = re.search(r'INSERT INTO \w+_new \(([^)]+)\)', src)
if m:
    cols = [c.strip() for c in m.group(1).split(',')]
    # Second column is the renamed one (after id)
    if len(cols) > 1:
        print(cols[1])
        sys.exit(0)
print('username')
sys.exit(0)
" 2>/dev/null || echo "username")

OLD_COL=$(python3 -c "
import re, sys
src = open('service_a/migrations/002_add_columns.py').read()
# Find the SELECT side of the INSERT...SELECT to get old column name
m = re.search(r'SELECT ([^F]+)FROM', src, re.DOTALL)
if m:
    cols = [c.strip() for c in m.group(1).split(',')]
    if len(cols) > 1:
        print(cols[1])
        sys.exit(0)
print('user_name')
sys.exit(0)
" 2>/dev/null || echo "user_name")

BOOL_COL=$(python3 -c "
import re, sys
src = open('service_a/migrations/002_add_columns.py').read()
# Find INTEGER DEFAULT 0 column (boolean)
m = re.search(r'(\w+) INTEGER DEFAULT 0', src)
if m:
    print(m.group(1))
    sys.exit(0)
print('email_verified')
" 2>/dev/null || echo "email_verified")

DATETIME_COL=$(python3 -c "
import re, sys
src = open('service_a/migrations/002_add_columns.py').read()
# Find TEXT DEFAULT NULL column (datetime)
m = re.search(r'(\w+) TEXT DEFAULT NULL', src)
if m:
    print(m.group(1))
    sys.exit(0)
print('last_login_at')
" 2>/dev/null || echo "last_login_at")

TIER_COL=$(python3 -c "
import re, sys
src = open('service_a/migrations/002_add_columns.py').read()
# Find TEXT DEFAULT '<value>' column (tier/level)
m = re.search(r\"(\w+) TEXT DEFAULT '([^']+)'\", src)
if m:
    print(m.group(1))
    sys.exit(0)
print('account_tier')
" 2>/dev/null || echo "account_tier")

DEFAULT_TIER=$(python3 -c "
import re, sys
src = open('service_a/migrations/002_add_columns.py').read()
m = re.search(r\"TEXT DEFAULT '([^']+)'\", src)
if m:
    print(m.group(1))
    sys.exit(0)
print('free')
" 2>/dev/null || echo "free")

TABLE_NAME=$(python3 -c "
import re, sys
src = open('service_a/migrations/002_add_columns.py').read()
m = re.search(r'CREATE TABLE (\w+)_new', src)
if m:
    print(m.group(1))
    sys.exit(0)
print('users')
" 2>/dev/null || echo "users")

# -------------------------------------------------------------------
# C1: pytest tests/ passes
# -------------------------------------------------------------------
if python3 -m pytest tests/ -q --tb=no 2>/dev/null | grep -q "passed"; then
    check "C1" "pytest tests/ passes" "pass"
else
    check "C1" "pytest tests/ did not pass" "fail"
fi

# -------------------------------------------------------------------
# C2: service_b/models.py has new column name (not old)
# -------------------------------------------------------------------
if python3 - "$NEW_COL" "$OLD_COL" <<'PYEOF' 2>/dev/null
import ast, sys
new_col = sys.argv[1]
old_col = sys.argv[2]
src = open('service_b/models.py').read()
# new column name appears
has_new = new_col in src
# old column name must not appear as attribute assignment (self.old_col)
has_old = f'self.{old_col}' in src or f'"{old_col}"' in src or f"'{old_col}'" in src
if has_new and not has_old:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C2" "service_b/models.py has renamed column (old name removed)" "pass"
else
    check "C2" "service_b/models.py still references old column name or missing new name" "fail"
fi

# -------------------------------------------------------------------
# C3: service_b/models.py has boolean column
# -------------------------------------------------------------------
if python3 - "$BOOL_COL" <<'PYEOF' 2>/dev/null
import sys
col = sys.argv[1]
src = open('service_b/models.py').read()
if col in src:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C3" "service_b/models.py has boolean column ($BOOL_COL)" "pass"
else
    check "C3" "service_b/models.py missing boolean column ($BOOL_COL)" "fail"
fi

# -------------------------------------------------------------------
# C4: service_b/models.py has datetime column
# -------------------------------------------------------------------
if python3 - "$DATETIME_COL" <<'PYEOF' 2>/dev/null
import sys
col = sys.argv[1]
src = open('service_b/models.py').read()
if col in src:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C4" "service_b/models.py has datetime column ($DATETIME_COL)" "pass"
else
    check "C4" "service_b/models.py missing datetime column ($DATETIME_COL)" "fail"
fi

# -------------------------------------------------------------------
# C5: service_b/models.py has tier/level column
# -------------------------------------------------------------------
if python3 - "$TIER_COL" <<'PYEOF' 2>/dev/null
import sys
col = sys.argv[1]
src = open('service_b/models.py').read()
if col in src:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C5" "service_b/models.py has tier/level column ($TIER_COL)" "pass"
else
    check "C5" "service_b/models.py missing tier/level column ($TIER_COL)" "fail"
fi

# -------------------------------------------------------------------
# C6: No SELECT * in service_b/queries.py
# -------------------------------------------------------------------
if ! grep -q "SELECT \*" service_b/queries.py 2>/dev/null; then
    check "C6" "No SELECT * in service_b/queries.py" "pass"
else
    check "C6" "service_b/queries.py still contains SELECT *" "fail"
fi

# -------------------------------------------------------------------
# C7: scripts/backfill.py is implemented (not just a stub)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('scripts/backfill.py').read()
tree = ast.parse(src)
# Must have more than just comments/pass/TODO
stmts = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.Call, ast.Assign, ast.Expr))]
# Exclude pure string constants (docstrings/comments)
real_stmts = [n for n in stmts if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
if len(real_stmts) >= 3:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C7" "scripts/backfill.py is implemented (not just a stub)" "pass"
else
    check "C7" "scripts/backfill.py appears to be an empty stub" "fail"
fi

# -------------------------------------------------------------------
# C8: backfill.py runs without error on a test DB
# -------------------------------------------------------------------
if python3 - "$TABLE_NAME" "$NEW_COL" "$BOOL_COL" "$DATETIME_COL" "$TIER_COL" "$DEFAULT_TIER" <<'PYEOF' 2>/dev/null
import sqlite3, sys, tempfile, os, importlib.util

table = sys.argv[1]
new_col = sys.argv[2]
bool_col = sys.argv[3]
dt_col = sys.argv[4]
tier_col = sys.argv[5]
default_tier = sys.argv[6]

# Create a temp DB with the new schema and an existing record
with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    db_path = f.name

conn = sqlite3.connect(db_path)
conn.execute(f"""
    CREATE TABLE {table} (
        id INTEGER PRIMARY KEY,
        {new_col} TEXT NOT NULL,
        email TEXT,
        {bool_col} INTEGER DEFAULT 0,
        {dt_col} TEXT DEFAULT NULL,
        {tier_col} TEXT DEFAULT '{default_tier}',
        created_at TEXT
    )
""")
conn.execute(f"INSERT INTO {table} (id, {new_col}, email, {bool_col}, {dt_col}, {tier_col}, created_at) VALUES (1, 'testuser', 'test@example.com', 0, NULL, NULL, '2024-01-01')")
conn.commit()
conn.close()

# Patch shared/database.py to use temp DB, then run backfill
os.environ['TEST_DB_PATH'] = db_path
import subprocess
result = subprocess.run(
    ['python3', 'scripts/backfill.py'],
    env={**os.environ, 'DB_PATH': db_path, 'DATABASE': db_path},
    capture_output=True, text=True, timeout=30
)
os.unlink(db_path)
if result.returncode == 0:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C8" "scripts/backfill.py runs without error" "pass"
else
    check "C8" "scripts/backfill.py failed to run" "fail"
fi

# -------------------------------------------------------------------
# C9: backfill sets boolean column to False (0) for existing records
# -------------------------------------------------------------------
if python3 - "$TABLE_NAME" "$NEW_COL" "$BOOL_COL" "$DATETIME_COL" "$TIER_COL" "$DEFAULT_TIER" <<'PYEOF' 2>/dev/null
import sqlite3, sys, tempfile, os, subprocess

table = sys.argv[1]
new_col = sys.argv[2]
bool_col = sys.argv[3]
dt_col = sys.argv[4]
tier_col = sys.argv[5]
default_tier = sys.argv[6]

with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    db_path = f.name

conn = sqlite3.connect(db_path)
conn.execute(f"""
    CREATE TABLE {table} (
        id INTEGER PRIMARY KEY,
        {new_col} TEXT NOT NULL,
        email TEXT,
        {bool_col} INTEGER DEFAULT 0,
        {dt_col} TEXT DEFAULT NULL,
        {tier_col} TEXT DEFAULT '{default_tier}',
        created_at TEXT
    )
""")
conn.execute(f"INSERT INTO {table} (id, {new_col}, email, {bool_col}, {dt_col}, {tier_col}, created_at) VALUES (1, 'alice', 'alice@example.com', 0, NULL, NULL, '2024-01-01')")
conn.commit()
conn.close()

result = subprocess.run(
    ['python3', 'scripts/backfill.py'],
    env={**os.environ, 'DB_PATH': db_path, 'DATABASE': db_path},
    capture_output=True, text=True, timeout=30
)

conn = sqlite3.connect(db_path)
row = conn.execute(f"SELECT {bool_col} FROM {table} WHERE id=1").fetchone()
conn.close()
os.unlink(db_path)

if row and row[0] in (0, False, None):
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C9" "backfill sets boolean column ($BOOL_COL) to False for existing records" "pass"
else
    check "C9" "backfill did not correctly set boolean column ($BOOL_COL)" "fail"
fi

# -------------------------------------------------------------------
# C10: backfill sets tier column to correct default from config
# -------------------------------------------------------------------
if python3 - "$TABLE_NAME" "$NEW_COL" "$BOOL_COL" "$DATETIME_COL" "$TIER_COL" "$DEFAULT_TIER" <<'PYEOF' 2>/dev/null
import sqlite3, sys, tempfile, os, subprocess

table = sys.argv[1]
new_col = sys.argv[2]
bool_col = sys.argv[3]
dt_col = sys.argv[4]
tier_col = sys.argv[5]
default_tier = sys.argv[6]

with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    db_path = f.name

conn = sqlite3.connect(db_path)
conn.execute(f"""
    CREATE TABLE {table} (
        id INTEGER PRIMARY KEY,
        {new_col} TEXT NOT NULL,
        email TEXT,
        {bool_col} INTEGER DEFAULT 0,
        {dt_col} TEXT DEFAULT NULL,
        {tier_col} TEXT DEFAULT NULL,
        created_at TEXT
    )
""")
conn.execute(f"INSERT INTO {table} (id, {new_col}, email, {bool_col}, {dt_col}, {tier_col}, created_at) VALUES (1, 'bob', 'bob@example.com', 0, NULL, NULL, '2024-01-01')")
conn.commit()
conn.close()

result = subprocess.run(
    ['python3', 'scripts/backfill.py'],
    env={**os.environ, 'DB_PATH': db_path, 'DATABASE': db_path},
    capture_output=True, text=True, timeout=30
)

conn = sqlite3.connect(db_path)
row = conn.execute(f"SELECT {tier_col} FROM {table} WHERE id=1").fetchone()
conn.close()
os.unlink(db_path)

if row and row[0] == default_tier:
    sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C10" "backfill sets tier column ($TIER_COL) to correct default ('$DEFAULT_TIER')" "pass"
else
    check "C10" "backfill did not set tier column ($TIER_COL) to correct default ('$DEFAULT_TIER')" "fail"
fi

# -------------------------------------------------------------------
# C11: both services import without error
# -------------------------------------------------------------------
if python3 -c "import service_a.models; import service_b.models" 2>/dev/null; then
    check "C11" "Both service_a.models and service_b.models import without error" "pass"
else
    check "C11" "One or both services fail to import" "fail"
fi

# -------------------------------------------------------------------
# C12: test_cross_service.py passes specifically
# -------------------------------------------------------------------
if python3 -m pytest tests/test_cross_service.py -q --tb=no 2>/dev/null | grep -q "passed"; then
    check "C12" "tests/test_cross_service.py passes" "pass"
else
    check "C12" "tests/test_cross_service.py did not pass" "fail"
fi

# -------------------------------------------------------------------
# Finalize score.json
# -------------------------------------------------------------------
partial_score=$(awk "BEGIN {printf \"%.4f\", $partial / $total}")
findings="${findings%,}"  # Remove trailing comma

cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {
    "partial_score": $partial_score,
    "checks_passed": $partial,
    "total_checks": $total
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
