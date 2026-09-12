#!/usr/bin/env bash
# Grader for TEST9: Mock-Based API Testing
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

# 1. service.py exists
check "test -f service.py" "missing_service"

# 2. test_service.py exists
check "test -f test_service.py" "missing_tests"

# 3. All tests pass
check "python3 -m pytest test_service.py -q 2>&1 | tail -1 | grep -q 'passed'" "tests_fail"

# 4. Minimum 8 test functions
check "python3 -c \"
import ast
with open('test_service.py') as f:
    tree = ast.parse(f.read())
test_fns = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith('test_')]
assert len(test_fns) >= 8, f'Only {len(test_fns)} test functions, need 8+'
\"" "too_few_tests"

# 5. Tests use mocking (unittest.mock or pytest-mock)
check "python3 -c \"
with open('test_service.py') as f:
    content = f.read()
assert 'mock' in content.lower() or 'Mock' in content or 'patch' in content, 'No mocking found'
\"" "no_mocking"

# 6. Error handling in service.py for timeout
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('service.py') as f:
    content = f.read()
fn_name = expected['timeout_function']
# Find the function and check for try/except
import ast
tree = ast.parse(content)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == fn_name:
        has_try = any(isinstance(child, ast.Try) for child in ast.walk(node))
        assert has_try, f'{fn_name} missing try/except for error handling'
        break
\"" "no_error_handling"

# 7. Tests cover all 3 API functions
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('test_service.py') as f:
    content = f.read()
for fn in expected['api_functions']:
    assert fn in content, f'No test for {fn}'
\"" "missing_api_coverage"

# 8. Tests include timeout/error scenario
check "python3 -c \"
with open('test_service.py') as f:
    content = f.read().lower()
assert 'timeout' in content or 'error' in content or 'exception' in content or 'side_effect' in content, 'No error scenario tests'
\"" "no_error_scenario"

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
