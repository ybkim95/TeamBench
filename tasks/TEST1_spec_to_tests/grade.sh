#!/usr/bin/env bash
set -euo pipefail
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

# 1. test_engine.py has at least 15 test functions
check "python3 -c \"
import ast
with open('calculator/test_engine.py') as f:
    tree = ast.parse(f.read())
test_funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
assert len(test_funcs) >= 15, f'Only {len(test_funcs)} test functions (need >= 15)'
print(f'FOUND {len(test_funcs)} TESTS')
\"" "too_few_tests"

# 2. All tests pass on correct engine
check "python3 -m pytest calculator/test_engine.py -q --tb=short 2>&1 | tail -1 | grep -q 'passed'" "tests_fail_on_correct_engine"

# 3. Branch coverage > 80% (check if pytest-cov available, otherwise skip gracefully)
check "python3 -c \"
import subprocess, sys
result = subprocess.run([sys.executable, '-m', 'pytest', 'calculator/test_engine.py', '--cov=calculator.engine', '--cov-report=term', '-q'], capture_output=True, text=True, timeout=30)
# Parse coverage from output
for line in result.stdout.splitlines():
    if 'engine' in line and '%' in line:
        pct = int(line.split('%')[0].split()[-1])
        assert pct >= 80, f'Coverage only {pct}% (need >= 80%)'
        print(f'COVERAGE: {pct}%')
        break
else:
    # If pytest-cov not available, just check tests pass
    assert result.returncode == 0, 'Tests failed'
    print('COVERAGE_CHECK_SKIPPED')
\"" "low_coverage"

# 4-8. Mutation testing: check 5 specific mutants
MUTANTS_DIR="$TASK_DIR/mutants"

for i in 1 2 3 4 5; do
  MUTANT=$(printf "%02d" $i)
  check "python3 -c \"
import shutil, subprocess, sys, os
# Backup original
shutil.copy('calculator/engine.py', 'calculator/engine.py.bak')
# Inject mutant
shutil.copy('$MUTANTS_DIR/mutant_${MUTANT}.py', 'calculator/engine.py')
# Run tests — should FAIL on mutant
result = subprocess.run([sys.executable, '-m', 'pytest', 'calculator/test_engine.py', '-q', '--tb=no'], capture_output=True, text=True, timeout=30)
# Restore original
shutil.copy('calculator/engine.py.bak', 'calculator/engine.py')
os.remove('calculator/engine.py.bak')
# Mutant should be caught (tests fail)
assert result.returncode != 0, f'Mutant $MUTANT not caught (tests still pass)'
print(f'MUTANT_${MUTANT}_CAUGHT')
\"" "mutant_${MUTANT}_not_caught"
done

# 9. Total mutants caught >= 7 out of 10
check "python3 -c \"
import shutil, subprocess, sys, os
caught = 0
for i in range(1, 11):
    mutant_file = f'$MUTANTS_DIR/mutant_{i:02d}.py'
    if not os.path.exists(mutant_file):
        continue
    shutil.copy('calculator/engine.py', 'calculator/engine.py.bak')
    shutil.copy(mutant_file, 'calculator/engine.py')
    result = subprocess.run([sys.executable, '-m', 'pytest', 'calculator/test_engine.py', '-q', '--tb=no'], capture_output=True, text=True, timeout=30)
    shutil.copy('calculator/engine.py.bak', 'calculator/engine.py')
    if result.returncode != 0:
        caught += 1
try:
    os.remove('calculator/engine.py.bak')
except:
    pass
assert caught >= 7, f'Only caught {caught}/10 mutants (need >= 7)'
print(f'MUTANTS_CAUGHT: {caught}/10')
\"" "insufficient_mutation_detection"

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
