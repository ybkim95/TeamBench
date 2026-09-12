#!/usr/bin/env bash
set -o pipefail
WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"

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

EXPECTED_JSON="$REPORTS/expected.json"
if [ ! -f "$EXPECTED_JSON" ]; then
  EXPECTED_JSON="$(dirname "$0")/expected.json"
fi

HOST_VAR="DATABASE_HOST"
PORT_VAR="DATABASE_PORT"
PK_COL="id"
if [ -f "$EXPECTED_JSON" ]; then
  HOST_VAR=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('host_var','DATABASE_HOST'))" 2>/dev/null || echo "DATABASE_HOST")
  PORT_VAR=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('port_var','DATABASE_PORT'))" 2>/dev/null || echo "DATABASE_PORT")
  PK_COL=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('pk_col','id'))" 2>/dev/null || echo "id")
fi

# 1. deploy.sh exports correct host variable
check "grep -q '${HOST_VAR}' deploy.sh" "deploy_wrong_host_var"

# 2. deploy.sh exports correct port variable
check "grep -q '${PORT_VAR}' deploy.sh" "deploy_wrong_port_var"

# 3. deploy.sh does NOT use the wrong variable names
check "! grep -q 'DB_HOST=' deploy.sh && ! grep -q 'DB_PORT=' deploy.sh" \
      "deploy_still_has_old_vars"

# 4. SQL FK references correct PK column
check "python3 -c \"
content = open('migrations/002_add_fk.sql').read().lower()
assert '(${PK_COL})' in content or '( ${PK_COL} )' in content or '(${PK_COL} )' in content, 'FK does not reference ${PK_COL}'
print('FK_OK')
\"" "sql_fk_wrong_column"

# 5. SQL FK does NOT reference wrong column
check "python3 -c \"
content = open('migrations/002_add_fk.sql').read().lower()
assert 'user_id)' not in content and '( user_id' not in content, 'FK still references user_id'
print('FK_NO_OLD')
\"" "sql_fk_still_wrong"

# 6. Python config loader defaults to ./config.env
check "python3 -c \"
source = open('app.py').read()
assert '/etc/app/config.env' not in source, 'Still using /etc/app/config.env'
assert 'config.env' in source, 'Missing config.env reference'
print('PATH_OK')
\"" "python_wrong_config_path"

# 7. Python config loader works with local config.env
check "python3 -c \"
import sys, os
sys.path.insert(0, '.')
from app import load_config
cfg = load_config()
assert cfg is not None, 'Config is None'
print('LOAD_OK')
\"" "config_load_fails"

# 8. test_app.py passes
check "python3 -m pytest test_app.py -q 2>/dev/null || python3 -m unittest test_app 2>/dev/null" \
      "tests_fail"

# 9. SQL schema is valid (001 + 002 can be applied)
check "python3 -c \"
import sqlite3
conn = sqlite3.connect(':memory:')
conn.execute('PRAGMA foreign_keys = ON')
with open('migrations/001_create.sql') as f:
    conn.executescript(f.read())
with open('migrations/002_add_fk.sql') as f:
    conn.executescript(f.read())
print('SCHEMA_OK')
\"" "sql_schema_invalid"

# 10. Attestation
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then SUCCESS=1; PASS=true; else SUCCESS=0; PASS=false; fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {"checks_passed": $PASSED, "checks_total": $CHECKS, "partial_score": $PARTIAL},
  "failure_modes": $FM
}
JSON
