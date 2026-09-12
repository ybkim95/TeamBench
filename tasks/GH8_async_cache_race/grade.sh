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
check "python3 -c 'import ast; ast.parse(open(\"dependency_injection.py\").read())'" "python_syntax_invalid"

# 2. test_single_request passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_injection import test_single_request; test_single_request()\"" "test_single_request_failed"

# 3. test_concurrent_race passes (core fix)
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_injection import test_concurrent_race; test_concurrent_race()\"" "test_concurrent_race_failed"

# 4. test_no_cache_works passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_injection import test_no_cache_works; test_no_cache_works()\"" "test_no_cache_works_failed"

# 5. test_dependency_chain passes
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_injection import test_dependency_chain; test_dependency_chain()\"" "test_dependency_chain_failed"

# 6. test_many_concurrent passes (core fix)
check "python3 -c \"import sys; sys.path.insert(0, '.'); from test_injection import test_many_concurrent; test_many_concurrent()\"" "test_many_concurrent_failed"

# 7. DependencyResolver class still present
check "python3 -c \"import sys; sys.path.insert(0, '.'); from dependency_injection import DependencyResolver\"" "dependency_resolver_missing"

# 8. No eval/exec
check "! grep -Eq '\b(eval|exec)\s*\(' dependency_injection.py" "eval_exec_found"

# 9. Attestation
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
