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

# 1. test_mathlib.py exists
check "test -f tests/test_mathlib.py" "test_file_missing"

# 2. At least 25 test functions
check "python3 -c \"
import ast
with open('tests/test_mathlib.py') as f:
    tree = ast.parse(f.read())
test_funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
assert len(test_funcs) >= 25, f'Only {len(test_funcs)} test functions (need >= 25)'
print(f'FOUND {len(test_funcs)} TESTS')
\"" "too_few_tests"

# 3. All tests pass on correct mathlib
check "python3 -m pytest tests/test_mathlib.py -q --tb=short 2>&1 | tail -1 | grep -q 'passed'" "tests_fail_on_correct_lib"

# 4. Tests cover error-raising paths (check for MathLibError in test file)
check "python3 -c \"
with open('tests/test_mathlib.py') as f:
    content = f.read()
assert 'MathLibError' in content, 'Tests must check MathLibError exceptions'
assert content.count('pytest.raises') >= 5 or content.count('raises') >= 5, 'Need at least 5 exception tests'
print('ERROR_TESTS_FOUND')
\"" "insufficient_error_tests"

# 5-8. Check 4 specific mutants are caught
MUTANTS_DIR="$TASK_DIR/mutants"
if [ ! -d "$MUTANTS_DIR" ]; then
  MUTANTS_DIR="$WORKSPACE/mutants"
fi

for i in 1 5 10 15; do
  MUTANT=$(printf "%02d" $i)
  check "python3 -c \"
import shutil, subprocess, sys, os
shutil.copy('mathlib.py', 'mathlib.py.bak')
shutil.copy('$MUTANTS_DIR/mutant_${MUTANT}.py', 'mathlib.py')
result = subprocess.run([sys.executable, '-m', 'pytest', 'tests/test_mathlib.py', '-q', '--tb=no'], capture_output=True, text=True, timeout=60)
shutil.copy('mathlib.py.bak', 'mathlib.py')
os.remove('mathlib.py.bak')
assert result.returncode != 0, f'Mutant $MUTANT not caught (tests still pass)'
print(f'MUTANT_${MUTANT}_CAUGHT')
\"" "mutant_${MUTANT}_not_caught"
done

# 9. Total mutants caught >= 16 out of 20
check "python3 -c \"
import shutil, subprocess, sys, os
caught = 0
for i in range(1, 21):
    mutant_file = f'$MUTANTS_DIR/mutant_{i:02d}.py'
    if not os.path.exists(mutant_file):
        continue
    shutil.copy('mathlib.py', 'mathlib.py.bak')
    shutil.copy(mutant_file, 'mathlib.py')
    result = subprocess.run([sys.executable, '-m', 'pytest', 'tests/test_mathlib.py', '-q', '--tb=no'], capture_output=True, text=True, timeout=60)
    shutil.copy('mathlib.py.bak', 'mathlib.py')
    if result.returncode != 0:
        caught += 1
try:
    os.remove('mathlib.py.bak')
except:
    pass
assert caught >= 16, f'Only caught {caught}/20 mutants (need >= 16)'
print(f'MUTANTS_CAUGHT: {caught}/20')
\"" "insufficient_mutation_detection"

# 10. Tests cover statistics functions
check "python3 -c \"
with open('tests/test_mathlib.py') as f:
    content = f.read()
stats_fns = ['mean', 'median', 'mode', 'std_dev', 'percentile']
found = sum(1 for fn in stats_fns if fn in content)
assert found >= 4, f'Only {found}/5 statistics functions tested (need >= 4)'
print(f'STATS_COVERAGE: {found}/5')
\"" "low_stats_coverage"

# 11. Tests cover prime/fibonacci/factorial
check "python3 -c \"
with open('tests/test_mathlib.py') as f:
    content = f.read()
combo_fns = ['is_prime', 'fibonacci', 'factorial']
found = sum(1 for fn in combo_fns if fn in content)
assert found >= 3, f'Only {found}/3 combinatorics functions tested (need all 3)'
print(f'COMBO_COVERAGE: {found}/3')
\"" "low_combo_coverage"

# 12. Attestation
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
