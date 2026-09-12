#!/usr/bin/env bash
# Grade script for LH7: Zero-Downtime Database Migration
# Arguments:
#   $1 = WORKSPACE  (directory containing app.py, migrations/, etc.)
#   $2 = REPORTS    (grader-only directory; contains expected.json)
#   $3 = SUBMISSION (directory where the agent writes attestation.json)
#   $4 = TASK_DIR   (task definition directory)
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

EXPECTED="$REPORTS/expected.json"
TABLE=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['table'])" 2>/dev/null)
OLD_COL=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['old_col'])" 2>/dev/null)
NEW_FIRST=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['new_col_first'])" 2>/dev/null)
NEW_LAST=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['new_col_last'])" 2>/dev/null)

# ── Check 1: Migration files exist ──────────────────────────────────────
check "python3 -c \"
import os
mig_dir = 'migrations'
scripts = [f for f in os.listdir(mig_dir) if f.endswith('.py') and f != '__init__.py']
assert len(scripts) >= 4, f'Only {len(scripts)} migration scripts (need >= 4)'
print(f'FOUND {len(scripts)} MIGRATION SCRIPTS')
\"" "insufficient_migration_files"

# ── Check 2: First migration adds nullable columns (Step 1) ────────────
check "python3 -c \"
import os
mig_dir = 'migrations'
scripts = sorted(f for f in os.listdir(mig_dir) if f.endswith('.py') and f != '__init__.py')
first = scripts[0]
with open(os.path.join(mig_dir, first)) as f:
    src = f.read().lower()
assert 'add' in src or 'alter' in src, f'First migration {first} does not add columns'
assert 'null' in src, f'First migration {first} does not mention nullable'
assert '$NEW_FIRST'.lower() in src or '$NEW_LAST'.lower() in src, \
    f'First migration does not reference new column names'
print(f'STEP1_OK: {first} adds nullable columns')
\"" "wrong_first_migration"

# ── Check 3: Second migration performs backfill (Step 2) ────────────────
check "python3 -c \"
import os
mig_dir = 'migrations'
scripts = sorted(f for f in os.listdir(mig_dir) if f.endswith('.py') and f != '__init__.py')
second = scripts[1]
with open(os.path.join(mig_dir, second)) as f:
    src = f.read().lower()
assert 'backfill' in src or 'update' in src or 'select' in src, \
    f'Second migration {second} does not perform backfill'
print(f'STEP2_OK: {second} performs backfill')
\"" "wrong_second_migration"

# ── Check 4: Third migration switches reads (Step 3) ───────────────────
check "python3 -c \"
import os
mig_dir = 'migrations'
scripts = sorted(f for f in os.listdir(mig_dir) if f.endswith('.py') and f != '__init__.py')
third = scripts[2]
with open(os.path.join(mig_dir, third)) as f:
    src = f.read().lower()
assert 'switch' in src or 'read' in src or 'flag' in src or 'feature' in src, \
    f'Third migration {third} does not switch reads'
print(f'STEP3_OK: {third} switches reads')
\"" "wrong_third_migration"

# ── Check 5: Fourth migration drops old column (Step 4) ────────────────
check "python3 -c \"
import os
mig_dir = 'migrations'
scripts = sorted(f for f in os.listdir(mig_dir) if f.endswith('.py') and f != '__init__.py')
fourth = scripts[3]
with open(os.path.join(mig_dir, fourth)) as f:
    src = f.read().lower()
assert 'drop' in src, f'Fourth migration {fourth} does not drop old column'
print(f'STEP4_OK: {fourth} drops old column')
\"" "wrong_fourth_migration"

# ── Check 6: Backfill completeness check exists in drop migration ──────
check "python3 -c \"
import os
mig_dir = 'migrations'
scripts = sorted(f for f in os.listdir(mig_dir) if f.endswith('.py') and f != '__init__.py')
fourth = scripts[3]
with open(os.path.join(mig_dir, fourth)) as f:
    src = f.read()
# Must check for NULL values before dropping
has_null_check = 'NULL' in src or 'null' in src.lower()
has_count_check = 'count' in src.lower() or 'select' in src.lower() or 'fetchall' in src.lower() or 'fetchone' in src.lower()
has_assert_or_raise = 'assert' in src or 'raise' in src or 'RuntimeError' in src or 'ValueError' in src
assert has_null_check and (has_count_check or has_assert_or_raise), \
    f'Fourth migration missing backfill completeness check (NULL check + assertion)'
print('BACKFILL_CHECK_OK')
\"" "missing_backfill_check"

# ── Check 7: app.py has new columns in model ───────────────────────────
check "python3 -c \"
with open('app.py') as f:
    src = f.read()
assert '$NEW_FIRST' in src, 'app.py missing new column $NEW_FIRST'
assert '$NEW_LAST' in src, 'app.py missing new column $NEW_LAST'
print('MODEL_UPDATED')
\"" "model_not_updated"

# ── Check 8: app.py is valid Python ────────────────────────────────────
check "python3 -c \"
import py_compile
py_compile.compile('app.py', doraise=True)
print('SYNTAX_OK')
\"" "app_syntax_error"

# ── Check 9: All migration files are valid Python ──────────────────────
check "python3 -c \"
import os, py_compile
mig_dir = 'migrations'
for f in sorted(os.listdir(mig_dir)):
    if f.endswith('.py') and f != '__init__.py':
        py_compile.compile(os.path.join(mig_dir, f), doraise=True)
print('ALL_MIGRATIONS_VALID_PYTHON')
\"" "migration_syntax_error"

# ── Check 10: run_migrations.py executes successfully end-to-end ───────
check "python3 -c \"
import subprocess, sys, os
# Clean up any previous DB
if os.path.exists('app.db'):
    os.remove('app.db')
if os.path.exists('migration_flags.json'):
    os.remove('migration_flags.json')

# Seed data first
result1 = subprocess.run([sys.executable, 'app.py'],
    capture_output=True, text=True, timeout=30)
assert result1.returncode == 0, f'app.py failed: {result1.stderr}'

# Run migrations
result2 = subprocess.run([sys.executable, 'run_migrations.py'],
    capture_output=True, text=True, timeout=60)
assert result2.returncode == 0, f'run_migrations.py failed: {result2.stderr}'
print('MIGRATIONS_COMPLETE')
\"" "migrations_fail"

# ── Check 11: Attestation ──────────────────────────────────────────────
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
