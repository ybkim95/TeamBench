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

# 1. test_calculator.py exists
check "test -f test_calculator.py" "test_file_missing"

# 2. All tests pass on fixed calculator.py
check "python3 -m pytest test_calculator.py -q --tb=short 2>&1 | tail -1 | grep -q 'passed'" "tests_fail_on_fixed_code"

# 3. Test count >= number of bugs (read from expected.json)
check "python3 -c \"
import ast, json, os, sys
expected_path = os.path.join('$REPORTS', '../expected.json')
# Try a few candidate paths
for candidate in [
    os.path.join('$REPORTS', '../expected.json'),
    os.path.join('$REPORTS', 'expected.json'),
]:
    if os.path.exists(candidate):
        expected_path = candidate
        break
with open('test_calculator.py') as f:
    tree = ast.parse(f.read())
test_funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
min_tests = 3  # fallback if expected.json unavailable
if os.path.exists(expected_path):
    data = json.load(open(expected_path))
    min_tests = data.get('min_tests', 3)
assert len(test_funcs) >= min_tests, f'Only {len(test_funcs)} test functions (need >= {min_tests})'
print(f'FOUND {len(test_funcs)} TESTS (need >= {min_tests})')
\"" "too_few_tests"

# 4. Tests use assertions (not print-only)
check "python3 -c \"
import ast
with open('test_calculator.py') as f:
    tree = ast.parse(f.read())
asserts = [n for n in ast.walk(tree) if isinstance(n, (ast.Assert, ast.Call))]
# Look for assert statements or pytest.raises usage
assert_stmts = [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]
raises_calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and
    hasattr(n.func, 'attr') and n.func.attr == 'raises']
total = len(assert_stmts) + len(raises_calls)
assert total >= 1, f'No assert statements or pytest.raises found'
print(f'ASSERTIONS_FOUND: {total}')
\"" "no_assertions"

# 5. pytest exits cleanly (exit code 0) on fixed module
check "python3 -m pytest test_calculator.py -q --tb=no 2>&1; test \${PIPESTATUS[0]} -eq 0" "pytest_nonzero_exit"

# 6-10. Each buggy variant is detected (each bug reintroduced must cause test failure)
# Read bug IDs from expected.json or fall back to scanning buggy_variants/
BUGGY_DIR="$WORKSPACE/buggy_variants"

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

caught = 0
total = len(variant_files)
details = []

for vf in variant_files:
    bug_id = vf.replace('.py', '')
    # Backup fixed calculator
    shutil.copy('calculator.py', 'calculator.py.bak')
    # Inject buggy variant
    shutil.copy(os.path.join(buggy_dir, vf), 'calculator.py')
    # Run tests — should FAIL on buggy code
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', 'test_calculator.py', '-q', '--tb=no'],
        capture_output=True, text=True, timeout=30
    )
    # Restore fixed
    shutil.copy('calculator.py.bak', 'calculator.py')
    if result.returncode != 0:
        caught += 1
        details.append(f'{bug_id}: CAUGHT')
    else:
        details.append(f'{bug_id}: MISSED')

try:
    os.remove('calculator.py.bak')
except:
    pass

print('\\n'.join(details))
assert caught == total, f'Only caught {caught}/{total} bugs'
print(f'ALL_BUGS_CAUGHT: {caught}/{total}')
\"" "some_bugs_not_detected"

# Individual checks for first 4 bug variants (checks 6-9)
VARIANT_NUM=0
for VARIANT_FILE in "$BUGGY_DIR"/*.py; do
  [ -f "$VARIANT_FILE" ] || continue
  VARIANT_NUM=$((VARIANT_NUM + 1))
  [ $VARIANT_NUM -gt 4 ] && break
  BUG_ID=$(basename "$VARIANT_FILE" .py)
  check "python3 -c \"
import shutil, subprocess, sys, os
shutil.copy('calculator.py', 'calculator.py.bak')
shutil.copy('$VARIANT_FILE', 'calculator.py')
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'test_calculator.py', '-q', '--tb=no'],
    capture_output=True, text=True, timeout=30
)
shutil.copy('calculator.py.bak', 'calculator.py')
try:
    os.remove('calculator.py.bak')
except:
    pass
assert result.returncode != 0, 'Bug not detected: $BUG_ID'
print('CAUGHT: $BUG_ID')
\"" "bug_${BUG_ID}_not_detected"
done

# 10. Attestation
check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass'
\" '$SUBMISSION/attestation.json'" "bad_attestation"

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
