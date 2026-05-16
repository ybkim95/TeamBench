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
check "python3 -c 'import ast; ast.parse(open(\"middleware.py\").read())'" "python_syntax_invalid"

# 2. test_basic_middleware passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_middleware import test_basic_middleware; test_basic_middleware()\"" "test_basic_middleware_failed"

# 3. test_error_handler_catches_next passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_middleware import test_error_handler_catches_next; test_error_handler_catches_next()\"" "test_error_handler_catches_next_failed"

# 4. test_error_handler_catches_downstream passes (core fix)
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_middleware import test_error_handler_catches_downstream; test_error_handler_catches_downstream()\"" "test_error_handler_catches_downstream_failed"

# 5. test_multiple_error_handlers passes (core fix)
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_middleware import test_multiple_error_handlers; test_multiple_error_handlers()\"" "test_multiple_error_handlers_failed"

# 6. test_middleware_order_preserved passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_middleware import test_middleware_order_preserved; test_middleware_order_preserved()\"" "test_middleware_order_preserved_failed"

# 7. test_error_handler_response passes (core fix)
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_middleware import test_error_handler_response; test_error_handler_response()\"" "test_error_handler_response_failed"

# 8. test_no_error_passthrough passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_middleware import test_no_error_passthrough; test_no_error_passthrough()\"" "test_no_error_passthrough_failed"

# 9. Pipeline class still present
check "python3 -c \"import sys; sys.path.insert(0, '.'); from middleware import Pipeline; assert hasattr(Pipeline, 'execute')\"" "pipeline_class_missing"

# 10. No eval/exec
check "! grep -Eq '\b(eval|exec)\s*\(' middleware.py" "eval_exec_found"

# 11. Attestation
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
