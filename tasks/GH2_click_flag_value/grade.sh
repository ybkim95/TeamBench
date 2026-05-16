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
check "python3 -m py_compile cli_parser.py" "syntax_error"

# 2. = sign handling still present (tokenizer intact)
check "grep -qE 'partition|split.*=|\"=\"' cli_parser.py" "tokenizer_broken"

# 3. No eval/exec introduced
check "! grep -qE '^\s*(eval|exec)\s*\(' cli_parser.py" "eval_exec_introduced"

# 4. test_flag_value_without_arg (core regression fix)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_cli import test_flag_value_without_arg
test_flag_value_without_arg()
\"" "flag_value_not_used"

# 5. test_flag_value_with_explicit_arg (must not break)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_cli import test_flag_value_with_explicit_arg
test_flag_value_with_explicit_arg()
\"" "explicit_arg_broken"

# 6. test_flag_value_with_equals (must not break)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_cli import test_flag_value_with_equals
test_flag_value_with_equals()
\"" "equals_syntax_broken"

# 7. test_regular_flag_still_works (must not break)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_cli import test_regular_flag_still_works
test_regular_flag_still_works()
\"" "boolean_flag_broken"

# 8. test_positional_not_consumed (critical regression)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_cli import test_positional_not_consumed
test_positional_not_consumed()
\"" "positional_consumed_by_flag"

# 9. test_help_generation (must not break)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_cli import test_help_generation
test_help_generation()
\"" "help_generation_broken"

# 10. Attestation
check "python3 -c \"
import json, sys
att = json.load(open(sys.argv[1]))
assert att.get('verdict') == 'pass'
\" '$SUBMISSION/attestation.json'" "bad_attestation"

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
