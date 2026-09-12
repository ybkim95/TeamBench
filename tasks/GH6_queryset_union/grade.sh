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

# Helper: run a single pytest test by node id
run_pytest() {
  python3 -m pytest "test_queryset.py::$1" -x -q --tb=no --no-header 2>/dev/null
}

# 1. Python syntax valid
check "python3 -c 'import ast; ast.parse(open(\"queryset.py\").read())'" "python_syntax_invalid"

# 2. test_basic_filter passes
check "run_pytest test_basic_filter" "test_basic_filter_failed"

# 3. test_basic_exclude passes
check "run_pytest test_basic_exclude" "test_basic_exclude_failed"

# 4. test_union_works passes
check "run_pytest test_union_works" "test_union_works_failed"

# 5. test_exclude_after_union passes (core fix)
check "run_pytest test_exclude_after_union" "test_exclude_after_union_failed"

# 6. test_filter_after_union passes (core fix)
check "run_pytest test_filter_after_union" "test_filter_after_union_failed"

# 7. test_chained_operations passes (core fix)
check "run_pytest test_chained_operations" "test_chained_operations_failed"

# 8. test_exclude_after_intersection passes (core fix)
check "run_pytest test_exclude_after_intersection" "test_exclude_after_intersection_failed"

# 9. test_union_without_filter passes
check "run_pytest test_union_without_filter" "test_union_without_filter_failed"

# 10. union method still in queryset.py
check "grep -q 'def union' queryset.py" "union_method_missing"

# 11. No eval/exec
check "! grep -Eq '\b(eval|exec)\s*\(' queryset.py" "eval_exec_found"

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
