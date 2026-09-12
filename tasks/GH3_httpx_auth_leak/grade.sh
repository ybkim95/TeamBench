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
check "python3 -c \"import ast; ast.parse(open('httpclient.py').read())\"" "syntax_error"

# 2. test_cross_origin_strips_auth (core security fix)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_security import test_cross_origin_strips_auth
test_cross_origin_strips_auth()
\"" "auth_header_leaked"

# 3. test_cross_origin_strips_cookies
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_security import test_cross_origin_strips_cookies
test_cross_origin_strips_cookies()
\"" "cookies_leaked"

# 4. test_same_origin_preserves_auth (must not break)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_security import test_same_origin_preserves_auth
test_same_origin_preserves_auth()
\"" "same_origin_auth_stripped"

# 5. test_same_origin_different_path (must not break)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_security import test_same_origin_different_path
test_same_origin_different_path()
\"" "same_origin_path_broken"

# 6. test_cross_origin_preserves_non_sensitive
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_security import test_cross_origin_preserves_non_sensitive
test_cross_origin_preserves_non_sensitive()
\"" "non_sensitive_headers_stripped"

# 7. test_multi_hop_redirect
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_security import test_multi_hop_redirect
test_multi_hop_redirect()
\"" "multi_hop_auth_leaked"

# 8. test_url_parsing (must not break)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_security import test_url_parsing
test_url_parsing()
\"" "url_parsing_broken"

# 9. test_max_redirects (must not break)
check "python3 -c \"
import sys; sys.path.insert(0, '.')
from test_security import test_max_redirects
test_max_redirects()
\"" "max_redirects_broken"

# 10. URL class still present
check "grep -q 'class URL' httpclient.py" "url_class_removed"

# 11. ConnectionPool code still present
check "grep -q 'ConnectionPool' httpclient.py" "connection_pool_removed"

# 12. No eval/exec introduced
check "! grep -qE '\beval\s*\(|\bexec\s*\(' httpclient.py" "eval_exec_introduced"

# 13. Attestation
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
