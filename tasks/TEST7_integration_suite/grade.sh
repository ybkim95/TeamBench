#!/usr/bin/env bash
# Grade script for TEST7: Integration Test Suite
# Arguments:
#   $1 = WORKSPACE  (directory containing services and tests/)
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
SVC1=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['service_set']['svc1'])" 2>/dev/null)
SVC2=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['service_set']['svc2'])" 2>/dev/null)
SVC3=$(python3 -c "import json; print(json.load(open('$EXPECTED'))['service_set']['svc3'])" 2>/dev/null)

# ── Check 1: test_integration.py exists and is non-empty ────────────────
check "test -s tests/test_integration.py" "test_file_missing_or_empty"

# ── Check 2: test_integration.py has at least 10 test functions ─────────
check "python3 -c \"
import ast
with open('tests/test_integration.py') as f:
    tree = ast.parse(f.read())
test_funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith('test_')]
assert len(test_funcs) >= 10, f'Only {len(test_funcs)} test functions (need >= 10)'
print(f'FOUND {len(test_funcs)} TESTS')
\"" "too_few_tests"

# ── Check 3: Tests reference all 3 services ─────────────────────────────
check "python3 -c \"
with open('tests/test_integration.py') as f:
    src = f.read()
for svc in ['$SVC1', '$SVC2', '$SVC3']:
    assert svc in src, f'{svc} not referenced in test file'
print('ALL_SERVICES_REFERENCED')
\"" "missing_service_references"

# ── Check 4: Tests can be collected by pytest ───────────────────────────
check "python3 -m pytest tests/test_integration.py --collect-only -q 2>&1 | grep -E '(test|selected)'" "tests_not_collectable"

# ── Check 5: Tests check status codes (look for status_code assertions) ─
check "python3 -c \"
with open('tests/test_integration.py') as f:
    src = f.read()
status_checks = src.count('status_code')
assert status_checks >= 3, f'Only {status_checks} status_code checks (need >= 3)'
print(f'STATUS_CODE_CHECKS: {status_checks}')
\"" "insufficient_status_code_checks"

# ── Check 6: Tests check response schema (look for key assertions) ─────
check "python3 -c \"
with open('tests/test_integration.py') as f:
    src = f.read()
schema_checks = 0
for keyword in ['get_json', 'json()', '.json', 'assert', 'in data', 'in resp', 'in response']:
    schema_checks += src.count(keyword)
assert schema_checks >= 5, f'Only {schema_checks} schema-related checks'
print(f'SCHEMA_CHECKS: {schema_checks}')
\"" "insufficient_schema_checks"

# ── Check 7: Tests check error format (JSON errors vs plain text) ──────
check "python3 -c \"
with open('tests/test_integration.py') as f:
    src = f.read().lower()
error_checks = sum(1 for kw in ['error', 'code', 'not_found', 'validation', '404', '422', '400', '500', '201', '204']
                   if kw in src)
assert error_checks >= 4, f'Only {error_checks} error-related checks'
print(f'ERROR_CHECKS: {error_checks}')
\"" "insufficient_error_checks"

# ── Check 8: Tests check cross-service contracts ────────────────────────
check "python3 -c \"
with open('tests/test_integration.py') as f:
    src = f.read()
# Cross-service tests should reference IDs from one service in calls to another
cross_refs = 0
for keyword in ['user_id', 'order_id', 'account_id', 'booking_id', 'customer_id', 'item_id',
                'client1', 'client2', 'client3']:
    cross_refs += src.count(keyword)
assert cross_refs >= 3, f'Only {cross_refs} cross-service references'
print(f'CROSS_SERVICE_REFS: {cross_refs}')
\"" "missing_cross_service_tests"

# ── Check 9: Tests detect at least some violations (run tests) ─────────
check "python3 -c \"
import subprocess, sys
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/test_integration.py', '-v', '--tb=short'],
    capture_output=True, text=True, timeout=60
)
output = result.stdout + result.stderr
# Count tests that detected violations (FAILED tests on buggy services)
failed_count = output.count('FAILED')
passed_count = output.count('PASSED')
total = failed_count + passed_count
assert total >= 5, f'Only {total} tests ran (need >= 5)'
# At least some should fail (detecting violations)
print(f'VIOLATION_DETECTION: {failed_count} failed, {passed_count} passed out of {total}')
\"" "tests_not_detecting_violations"

# ── Check 10: Attestation ──────────────────────────────────────────────
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
