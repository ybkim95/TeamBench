#!/usr/bin/env bash
# Seed-aware grader for CR5: Test Coverage — Add Tests for Uncovered Paths
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

# Read module name from expected.json (fallback: scan for known names)
MODULE_NAME=$(python3 -c "
import json, os
for candidate in ['$EXPECTED', '$REPORTS/../expected.json']:
    if os.path.exists(candidate):
        d = json.load(open(candidate))
        print(d.get('module_name', ''))
        break
" 2>/dev/null || echo "")

if [ -z "$MODULE_NAME" ]; then
  # Fallback: detect from workspace
  for name in payment inventory scheduler parser; do
    if [ -f "${name}.py" ]; then
      MODULE_NAME="$name"
      break
    fi
  done
fi

TEST_FILE="test_${MODULE_NAME}.py"
BUGGY_DIR="$WORKSPACE/buggy_variants"

# ── Check 1: test file exists ────────────────────────────────────────────────
check "test -f '$TEST_FILE'" "test_file_missing"

# ── Check 2: source module not modified ──────────────────────────────────────
# We verify the module can still be imported cleanly (syntax OK, not blanked)
check "python3 -c \"import importlib.util, sys; spec = importlib.util.spec_from_file_location('mod', '${MODULE_NAME}.py'); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)\"" "source_module_broken"

# ── Check 3: all tests pass on correct module ────────────────────────────────
check "python3 -m pytest '$TEST_FILE' -q --tb=short 2>&1 | grep -qE '(passed|no tests ran)'" "tests_fail_on_correct_code"

# ── Check 4: pytest exits with code 0 on correct module ─────────────────────
check "python3 -m pytest '$TEST_FILE' -q --tb=no; test \${PIPESTATUS[0]} -eq 0" "pytest_nonzero_exit"

# ── Check 5: minimum test function count ────────────────────────────────────
check "python3 -c \"
import ast, json, os
expected_path = '$EXPECTED'
for candidate in [expected_path, '$REPORTS/../expected.json']:
    if os.path.exists(candidate):
        expected_path = candidate
        break
with open('$TEST_FILE') as f:
    tree = ast.parse(f.read())
test_funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
min_tests = 5  # fallback
if os.path.exists(expected_path):
    data = json.load(open(expected_path))
    min_tests = data.get('min_new_tests', 5)
assert len(test_funcs) >= min_tests, f'Only {len(test_funcs)} test functions (need >= {min_tests})'
print(f'FOUND {len(test_funcs)} TESTS (need >= {min_tests})')
\"" "too_few_tests"

# ── Check 6: tests use real assertions ──────────────────────────────────────
check "python3 -c \"
import ast
with open('$TEST_FILE') as f:
    tree = ast.parse(f.read())
assert_stmts = [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]
raises_calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and
    hasattr(n.func, 'attr') and n.func.attr == 'raises']
total = len(assert_stmts) + len(raises_calls)
assert total >= 3, f'Only {total} assertions/pytest.raises found (need >= 3)'
print(f'ASSERTIONS_FOUND: {total}')
\"" "insufficient_assertions"

# ── Check 7: all buggy variants are caught ───────────────────────────────────
check "python3 -c \"
import shutil, subprocess, sys, os, json

buggy_dir = '$BUGGY_DIR'
if not os.path.isdir(buggy_dir):
    print('NO_BUGGY_VARIANTS_DIR')
    sys.exit(1)

variant_files = sorted(f for f in os.listdir(buggy_dir) if f.endswith('.py'))
if not variant_files:
    print('NO_BUGGY_VARIANTS')
    sys.exit(1)

module_name = '$MODULE_NAME'
caught = 0
total = len(variant_files)
details = []

for vf in variant_files:
    path_id = vf.replace('.py', '')
    # Backup correct module
    shutil.copy(f'{module_name}.py', f'{module_name}.py.bak')
    # Inject buggy variant
    shutil.copy(os.path.join(buggy_dir, vf), f'{module_name}.py')
    # Run tests — should FAIL on buggy code
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', '$TEST_FILE', '-q', '--tb=no'],
        capture_output=True, text=True, timeout=30
    )
    # Restore correct module
    shutil.copy(f'{module_name}.py.bak', f'{module_name}.py')
    if result.returncode != 0:
        caught += 1
        details.append(f'{path_id}: CAUGHT')
    else:
        details.append(f'{path_id}: MISSED')

try:
    os.remove(f'{module_name}.py.bak')
except:
    pass

print('\n'.join(details))
assert caught == total, f'Only caught {caught}/{total} uncovered paths'
print(f'ALL_PATHS_CAUGHT: {caught}/{total}')
\"" "some_paths_not_tested"

# ── Checks 8–12: individual path mutation checks (up to first 5 variants) ────
VARIANT_NUM=0
for VARIANT_FILE in "$BUGGY_DIR"/*.py; do
  [ -f "$VARIANT_FILE" ] || continue
  VARIANT_NUM=$((VARIANT_NUM + 1))
  [ $VARIANT_NUM -gt 5 ] && break
  PATH_ID=$(basename "$VARIANT_FILE" .py)
  check "python3 -c \"
import shutil, subprocess, sys, os
module_name = '$MODULE_NAME'
shutil.copy(f'{module_name}.py', f'{module_name}.py.bak')
shutil.copy('$VARIANT_FILE', f'{module_name}.py')
result = subprocess.run(
    [sys.executable, '-m', 'pytest', '$TEST_FILE', '-q', '--tb=no'],
    capture_output=True, text=True, timeout=30
)
shutil.copy(f'{module_name}.py.bak', f'{module_name}.py')
try:
    os.remove(f'{module_name}.py.bak')
except:
    pass
assert result.returncode != 0, 'Path not tested: $PATH_ID'
print('CAUGHT: $PATH_ID')
\"" "path_${PATH_ID}_not_tested"
done

# ── Attestation ───────────────────────────────────────────────────────────────
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

# ── Score output ──────────────────────────────────────────────────────────────
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
