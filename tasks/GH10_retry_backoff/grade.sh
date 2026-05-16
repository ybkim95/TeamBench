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
check "python3 -c 'import ast; ast.parse(open(\"task_queue.py\").read())'" "python_syntax_invalid"

# 2. test_basic_retry passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_retry import test_basic_retry; test_basic_retry()\"" "test_basic_retry_failed"

# 3. test_max_delay_cap passes (core fix)
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_retry import test_max_delay_cap; test_max_delay_cap()\"" "test_max_delay_cap_failed"

# 4. test_delay_never_negative passes (core fix)
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_retry import test_delay_never_negative; test_delay_never_negative()\"" "test_delay_never_negative_failed"

# 5. test_exponential_growth passes (core fix)
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_retry import test_exponential_growth; test_exponential_growth()\"" "test_exponential_growth_failed"

# 6. test_jitter_bounded passes (core fix)
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_retry import test_jitter_bounded; test_jitter_bounded()\"" "test_jitter_bounded_failed"

# 7. test_no_jitter passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_retry import test_no_jitter; test_no_jitter()\"" "test_no_jitter_failed"

# 8. test_max_retries_respected passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_retry import test_max_retries_respected; test_max_retries_respected()\"" "test_max_retries_respected_failed"

# 9. test_task_state_machine passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_retry import test_task_state_machine; test_task_state_machine()\"" "test_task_state_machine_failed"

# 10. RetryPolicy class still present
check "python3 -c \"import sys; sys.path.insert(0, '.'); from task_queue import RetryPolicy; p = RetryPolicy(); assert hasattr(p, 'max_retries') and hasattr(p, 'base_delay') and hasattr(p, 'max_delay') and hasattr(p, 'jitter') and hasattr(p, 'backoff_factor') and callable(getattr(p, 'calculate_delay', None))\"" "retry_policy_missing"

# 11. No eval/exec
check "! grep -Eq '\b(eval|exec)\s*\(' task_queue.py" "eval_exec_found"

# 12. Attestation
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
