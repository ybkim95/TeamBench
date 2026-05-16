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

# 1. Python syntax valid
check "python3 -c 'import ast; ast.parse(open(\"test_framework.py\").read())'" "python_syntax_invalid"

# 2. test_function_scope_isolation passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_fixtures import test_function_scope_isolation; test_function_scope_isolation()\"" "test_function_scope_isolation_failed"

# 3. test_session_scope_leak passes (core fix)
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_fixtures import test_session_scope_leak; test_session_scope_leak()\"" "test_session_scope_leak_failed"

# 4. test_session_scope_dict_leak passes (core fix)
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_fixtures import test_session_scope_dict_leak; test_session_scope_dict_leak()\"" "test_session_scope_dict_leak_failed"

# 5. test_session_immutable_cached passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_fixtures import test_session_immutable_cached; test_session_immutable_cached()\"" "test_session_immutable_cached_failed"

# 6. test_runner_integration passes (core fix)
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_fixtures import test_runner_integration; test_runner_integration()\"" "test_runner_integration_failed"

# 7. test_module_scope_works passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_fixtures import test_module_scope_works; test_module_scope_works()\"" "test_module_scope_works_failed"

# 8. FixtureManager class still present
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_framework import FixtureManager; mgr = FixtureManager(); assert hasattr(mgr, 'register') and hasattr(mgr, 'get_fixture') and hasattr(mgr, 'clear_scope')\"" "fixture_manager_missing"

# 9. No eval/exec
check "! grep -Eq '\b(eval|exec)\s*\(' test_framework.py" "eval_exec_found"

# 10. Attestation
check "test -f '$SUBMISSION/attestation.json'" "attestation_missing"

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
