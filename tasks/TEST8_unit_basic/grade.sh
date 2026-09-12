#!/usr/bin/env bash
# Grader for TEST8: Unit Test Basics
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
source /usr/local/lib/venv/bin/activate 2>/dev/null || true

# 1. mathutils.py exists
check "test -f mathutils.py" "missing_mathutils"

# 2. test_mathutils.py exists
check "test -f test_mathutils.py" "missing_tests"

# 3. All tests pass
check "python3 -m pytest test_mathutils.py -q 2>&1 | tail -1 | grep -q 'passed'" "tests_fail"

# 4. Bug 1 fixed (check via expected.json)
check "python3 -c \"
import json, importlib.util, sys
expected = json.load(open('$EXPECTED'))
spec = importlib.util.spec_from_file_location('mathutils', 'mathutils.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
fn = expected['bug1_function']
args = expected['bug1_args']
exp = expected['bug1_expected']
result = getattr(mod, fn)(*args)
assert result == exp, f'{fn}({args}) = {result}, expected {exp}'
\"" "bug1_not_fixed"

# 5. Bug 2 fixed
check "python3 -c \"
import json, importlib.util
expected = json.load(open('$EXPECTED'))
spec = importlib.util.spec_from_file_location('mathutils', 'mathutils.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
fn = expected['bug2_function']
args = expected['bug2_args']
exp = expected['bug2_expected']
exp_type = expected['bug2_expected_type']
result = getattr(mod, fn)(*args)
assert type(result).__name__ == exp_type, f'{fn} returned {type(result).__name__}, expected {exp_type}'
assert result == exp, f'{fn}({args}) = {result}, expected {exp}'
\"" "bug2_not_fixed"

# 6. Bug 3 fixed
check "python3 -c \"
import json, importlib.util
expected = json.load(open('$EXPECTED'))
spec = importlib.util.spec_from_file_location('mathutils', 'mathutils.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
fn = expected['bug3_function']
args = expected['bug3_args']
exp = expected['bug3_expected']
result = getattr(mod, fn)(*args)
assert result == exp, f'{fn}({args}) = {result}, expected {exp}'
\"" "bug3_not_fixed"

# 7. Minimum test count (6+)
check "python3 -c \"
import ast
with open('test_mathutils.py') as f:
    tree = ast.parse(f.read())
test_fns = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith('test_')]
assert len(test_fns) >= 6, f'Only {len(test_fns)} test functions, need 6+'
\"" "too_few_tests"

# Attestation
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
    PASS=true
else
    PASS=false
fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $([ "$PASS" = "true" ] && echo 1 || echo 0)},
  "secondary": {
    "checks_passed": $PASSED,
    "checks_total": $CHECKS,
    "partial_score": $PARTIAL
  },
  "failure_modes": $FM
}
JSON
