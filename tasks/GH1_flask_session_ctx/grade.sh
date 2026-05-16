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
check "python3 -c \"import ast; ast.parse(open('testclient.py').read())\"" "syntax_error"

# 2. HMAC still used for session signing (must not be removed)
check "grep -q 'hmac' testclient.py" "signing_removed"

# 3. No eval/exec introduced
check "! grep -qE '\beval\s*\(|\bexec\s*\(' testclient.py" "eval_exec_introduced"

# 4. test_session_works_without_redirect (baseline)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_app import test_session_works_without_redirect
test_session_works_without_redirect()
print('OK')
\"" "baseline_broken"

# 5. test_session_signing_intact (false positive — signing is correct)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_app import test_session_signing_intact
test_session_signing_intact()
print('OK')
\"" "signing_broken"

# 6. test_session_persists_on_redirect (core bug fix)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_app import test_session_persists_on_redirect
test_session_persists_on_redirect()
print('OK')
\"" "session_lost_on_redirect"

# 7. test_session_persists_multi_redirect (multi-hop)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_app import test_session_persists_multi_redirect
test_session_persists_multi_redirect()
print('OK')
\"" "session_lost_on_multi_redirect"

# 8. Attestation
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
