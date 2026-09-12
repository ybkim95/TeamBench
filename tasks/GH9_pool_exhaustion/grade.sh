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
check "python3 -c 'import ast; ast.parse(open(\"db_pool.py\").read())'" "python_syntax_invalid"

# 2. test_basic_query passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_pool import test_basic_query; test_basic_query()\"" "test_basic_query_failed"

# 3. test_query_error_handling passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_pool import test_query_error_handling; test_query_error_handling()\"" "test_query_error_handling_failed"

# 4. test_pool_exhaustion_on_errors passes (core fix)
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_pool import test_pool_exhaustion_on_errors; test_pool_exhaustion_on_errors()\"" "test_pool_exhaustion_on_errors_failed"

# 5. test_pool_status_after_errors passes (core fix)
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_pool import test_pool_status_after_errors; test_pool_status_after_errors()\"" "test_pool_status_after_errors_failed"

# 6. test_concurrent_after_errors passes (core fix)
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_pool import test_concurrent_after_errors; test_concurrent_after_errors()\"" "test_concurrent_after_errors_failed"

# 7. test_successful_queries_release passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_pool import test_successful_queries_release; test_successful_queries_release()\"" "test_successful_queries_release_failed"

# 8. test_pool_size_respected passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_pool import test_pool_size_respected; test_pool_size_respected()\"" "test_pool_size_respected_failed"

# 9. ConnectionPool class still present
check "python3 -c \"import sys; sys.path.insert(0, '.'); from db_pool import ConnectionPool\"" "connection_pool_missing"

# 10. No eval/exec
check "! grep -Eq '\b(eval|exec)\s*\(' db_pool.py" "eval_exec_found"

# 11. Attestation
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
