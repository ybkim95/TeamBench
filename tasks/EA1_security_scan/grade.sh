#!/usr/bin/env bash
# EA1 grader: verify security fixes and false positive preservation
set -euo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

pass=true
partial=0
total=8
findings=""

check() {
    local id="$1"
    local desc="$2"
    local result="$3"
    if [ "$result" = "pass" ]; then
        partial=$((partial + 1))
        findings="${findings}{\"id\":\"${id}\",\"ok\":true,\"note\":\"${desc}\"},"
    else
        pass=false
        findings="${findings}{\"id\":\"${id}\",\"ok\":false,\"note\":\"${desc}\"},"
    fi
}

# Check V1: SQL injection fixed (parameterized query)
if python3 -c "
import ast, sys
src = open('${WORKSPACE}/app/routes.py').read()
# Look for format string or % in SQL context vs parameterized
if 'SELECT' in src and ('format(' in src or '%' in src or 'f\"' in src):
    # Check if it's actually building a query string with user data
    tree = ast.parse(src)
    sys.exit(1)  # Still vulnerable
sys.exit(0)
" 2>/dev/null; then
    check "V1" "SQL injection fixed" "pass"
else
    check "V1" "SQL injection still present" "fail"
fi

# Check V2: Hardcoded secret fixed
if ! grep -q 'SECRET_KEY.*=.*"hardcoded_secret' "${WORKSPACE}/app/config.py" 2>/dev/null && \
   grep -q 'os.environ' "${WORKSPACE}/app/config.py" 2>/dev/null; then
    check "V2" "Hardcoded secret fixed" "pass"
else
    check "V2" "Hardcoded secret still present" "fail"
fi

# Check V3: eval() removed from routes
if ! grep -qE '^\s*result\s*=\s*eval\(' "${WORKSPACE}/app/routes.py" 2>/dev/null; then
    check "V3" "eval() removed" "pass"
else
    check "V3" "eval() still present" "fail"
fi

# Check V4: subprocess shell=False in utils
if ! grep -q 'shell=True' "${WORKSPACE}/app/utils.py" 2>/dev/null; then
    check "V4" "subprocess shell=True fixed" "pass"
else
    check "V4" "subprocess shell=True still present" "fail"
fi

# Check V5: MD5 removed from auth.py production code
if ! grep -q 'md5' "${WORKSPACE}/app/auth.py" 2>/dev/null; then
    check "V5" "MD5 removed from auth" "pass"
else
    check "V5" "MD5 still present in auth.py" "fail"
fi

# Check V6: defusedxml or safe XML
if grep -qE 'defusedxml|lxml.*resolve_entities.*False' "${WORKSPACE}/app/parser.py" 2>/dev/null; then
    check "V6" "XXE fixed with defusedxml" "pass"
else
    check "V6" "XXE still present in parser.py" "fail"
fi

# Check V7: pickle replaced with json
if ! grep -q 'pickle.loads' "${WORKSPACE}/app/cache.py" 2>/dev/null; then
    check "V7" "pickle.loads removed" "pass"
else
    check "V7" "pickle.loads still present" "fail"
fi

# Check V8: secrets module used
if grep -q 'secrets\.' "${WORKSPACE}/app/tokens.py" 2>/dev/null; then
    check "V8" "secrets module used for token generation" "pass"
else
    check "V8" "Insecure random still used in tokens.py" "fail"
fi

# Check FP1+FP2: tests/test_auth.py unchanged
if [ -f "${WORKSPACE}/tests/test_auth.py" ]; then
    fp_ok=true
    if ! grep -q 'TEST_PASSWORD' "${WORKSPACE}/tests/test_auth.py"; then
        fp_ok=false
        findings="${findings}{\"id\":\"FP_PRESERVED\",\"ok\":false,\"note\":\"test_auth.py was modified (TEST_PASSWORD removed)\"},"
    fi
    if ! grep -q 'test_legacy_hash_compatibility' "${WORKSPACE}/tests/test_auth.py"; then
        fp_ok=false
        findings="${findings}{\"id\":\"FP_PRESERVED\",\"ok\":false,\"note\":\"test_auth.py was modified (legacy test removed)\"},"
    fi
    if [ "$fp_ok" = "true" ]; then
        findings="${findings}{\"id\":\"FP_PRESERVED\",\"ok\":true,\"note\":\"False positives preserved in test fixtures\"},"
    else
        pass=false
    fi
fi

partial_score=$(echo "scale=2; $partial / $total" | bc)
findings="${findings%,}"  # Remove trailing comma

cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {
    "partial_score": $partial_score,
    "fixed_count": $partial,
    "total_vulns": $total
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF
