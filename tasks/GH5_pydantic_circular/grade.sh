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
check "python3 -c \"import ast; ast.parse(open('validator.py').read())\"" "syntax_error"

# 2. SchemaResolver class still present
check "grep -q 'class SchemaResolver' validator.py" "schema_resolver_removed"

# 3. No eval/exec introduced
check "! grep -qE '\beval\s*\(|\bexec\s*\(' validator.py" "eval_exec_introduced"

# 4. test_simple_model (must not break — non-recursive)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_validator import test_simple_model
test_simple_model()
\"" "simple_model_broken"

# 5. test_non_recursive_nested (must not break)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_validator import test_non_recursive_nested
test_non_recursive_nested()
\"" "nested_model_broken"

# 6. test_primitive_validation (must not break)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_validator import test_primitive_validation
test_primitive_validation()
\"" "primitive_validation_broken"

# 7. test_recursive_depth_1 (should work even buggy)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_validator import test_recursive_depth_1
test_recursive_depth_1()
\"" "depth_1_broken"

# 8. test_recursive_depth_3 (core bug — depth > 2 fails)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_validator import test_recursive_depth_3
test_recursive_depth_3()
\"" "depth_3_data_lost"

# 9. test_wide_recursive (core bug — nested children)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_validator import test_wide_recursive
test_wide_recursive()
\"" "wide_recursive_broken"

# 10. _build_model_instance still present
check "grep -q '_build_model_instance' validator.py" "build_model_removed"

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
