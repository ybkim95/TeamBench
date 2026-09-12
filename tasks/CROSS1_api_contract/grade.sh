#!/usr/bin/env bash
# CROSS1 grader: verify Python client matches Go server contract
set -uo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

cd "$WORKSPACE"

pass=true
partial=0
total=10
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

# Install dependencies
# was: pip install (grade-time network fetch), replaced scripts/make_graders_hermetic.py
tb_require pytest requests || true

# -------------------------------------------------------------------
# C1: Go server compiles (do not change Go source)
# -------------------------------------------------------------------
if (cd service && go build ./... 2>/dev/null); then
    check "C1" "Go server compiles successfully" "pass"
else
    check "C1" "Go server failed to compile" "fail"
fi

# -------------------------------------------------------------------
# C2: Python client imports without error
# -------------------------------------------------------------------
if python3 -c "from client.api import APIClient; from client.models import User; from client.exceptions import APIError, parse_error_response" 2>/dev/null; then
    check "C2" "Python client imports without error" "pass"
else
    check "C2" "Python client import failed" "fail"
fi

# -------------------------------------------------------------------
# C3: test_integration.py passes (end-to-end client-server)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_integration.py -q --tb=no 2>/dev/null | grep -q "passed"; then
    check "C3" "Integration tests pass (test_integration.py)" "pass"
else
    check "C3" "Integration tests failed (test_integration.py)" "fail"
fi

# -------------------------------------------------------------------
# C4: test_pagination.py passes
# -------------------------------------------------------------------
if python3 -m pytest tests/test_pagination.py -q --tb=no 2>/dev/null | grep -q "passed"; then
    check "C4" "Pagination tests pass (test_pagination.py)" "pass"
else
    check "C4" "Pagination tests failed (test_pagination.py)" "fail"
fi

# -------------------------------------------------------------------
# C5: test_errors.py passes
# -------------------------------------------------------------------
if python3 -m pytest tests/test_errors.py -q --tb=no 2>/dev/null | grep -q "passed"; then
    check "C5" "Error handling tests pass (test_errors.py)" "pass"
else
    check "C5" "Error handling tests failed (test_errors.py)" "fail"
fi

# -------------------------------------------------------------------
# C6: client/models.py uses camelCase userId (not snake_case user_id)
# Check that from_dict reads "userId" key, not "user_id"
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('client/models.py').read()
# Must have "userId" string literal somewhere in the file
if '"userId"' in src or "'userId'" in src:
    # Must NOT have the buggy pattern data.get("user_id") as the primary lookup
    # We allow user_id as the python attribute name, but from_dict must map "userId"
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'from_dict':
            func_src = ast.unparse(node)
            if '"userId"' in func_src or "'userId'" in func_src:
                sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C6" "client/models.py from_dict maps camelCase 'userId' key" "pass"
else
    check "C6" "client/models.py still uses snake_case 'user_id' key in from_dict" "fail"
fi

# -------------------------------------------------------------------
# C7: client/api.py parses "data" key for pagination (not "results")
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
src = open('client/api.py').read()
tree = ast.parse(src)
# Find list_* method and check it uses "data" key, not "results"
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name.startswith('list_'):
        func_src = ast.unparse(node)
        if ('"data"' in func_src or "'data'" in func_src) and \
           ('"results"' not in func_src and "'results'" not in func_src):
            sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C7" "client/api.py parses 'data' key for pagination results" "pass"
else
    check "C7" "client/api.py still uses 'results' key instead of 'data'" "fail"
fi

# -------------------------------------------------------------------
# C8: client/exceptions.py handles 422 status code (not just 400)
# Check that parse_error_response actually branches on 422 AND reads "errors" key
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('client/exceptions.py').read()
tree = ast.parse(src)

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'parse_error_response':
        func_src = ast.unparse(node)
        # Must contain 422 as a numeric literal (not just in a comment)
        has_422 = False
        for n in ast.walk(node):
            if isinstance(n, ast.Constant) and n.value == 422:
                has_422 = True
        # Must reference "errors" key (not just "error")
        has_errors_key = ('"errors"' in func_src or "'errors'" in func_src)
        if has_422 and has_errors_key:
            sys.exit(0)
sys.exit(1)
PYEOF
then
    check "C8" "client/exceptions.py handles HTTP 422 with 'errors' array" "pass"
else
    check "C8" "client/exceptions.py still expects 400 with single 'error' string" "fail"
fi

# -------------------------------------------------------------------
# C9: api_spec.yaml updated to match actual server contract
# Check YAML structure: data/next keys present, 422 response present,
# errors array type present, userId field present.
# Use line-by-line checks to avoid matching YAML comments.
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import sys, re

try:
    with open('api_spec.yaml') as f:
        lines = f.readlines()
except FileNotFoundError:
    sys.exit(1)

# Strip comment portions from each line before checking
stripped = []
for line in lines:
    # Remove inline YAML comments (everything after unquoted #)
    code_part = re.sub(r'\s*#.*$', '', line)
    stripped.append(code_part)

content = ''.join(stripped)

# Must have "data:" as a YAML key (pagination items)
if not re.search(r'^\s+data\s*:', content, re.MULTILINE):
    print("Missing 'data:' key", file=sys.stderr); sys.exit(1)

# Must have "next:" as a YAML key (pagination cursor)
if not re.search(r'^\s+next\s*:', content, re.MULTILINE):
    print("Missing 'next:' key", file=sys.stderr); sys.exit(1)

# Must have "422" as a response status
if '"422"' not in content and "'422'" not in content and '422:' not in content:
    print("Missing 422 response", file=sys.stderr); sys.exit(1)

# Must have "errors:" as a YAML key (error array field)
if not re.search(r'^\s+errors\s*:', content, re.MULTILINE):
    print("Missing 'errors:' key", file=sys.stderr); sys.exit(1)

# Must have userId (camelCase) as a field name
if 'userId' not in content and 'productId' not in content and 'orderId' not in content:
    print("Missing camelCase id field", file=sys.stderr); sys.exit(1)

sys.exit(0)
PYEOF
then
    check "C9" "api_spec.yaml updated with correct contract (userId/productId/orderId, data, next, 422, errors)" "pass"
else
    check "C9" "api_spec.yaml not fully updated to match server contract" "fail"
fi

# -------------------------------------------------------------------
# C10: Python syntax validity (client files parseable)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys
files = ['client/api.py', 'client/models.py', 'client/exceptions.py']
for f in files:
    try:
        ast.parse(open(f).read())
    except SyntaxError as e:
        print(f"Syntax error in {f}: {e}", file=sys.stderr)
        sys.exit(1)
sys.exit(0)
PYEOF
then
    check "C10" "All Python client files have valid syntax" "pass"
else
    check "C10" "Syntax error found in Python client files" "fail"
fi

# -------------------------------------------------------------------
# Run full pytest (informational counts)
# -------------------------------------------------------------------
pytest_out=$(python3 -m pytest tests/ -q --tb=no 2>&1 || true)
pytest_pass=$(echo "$pytest_out" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
pytest_fail=$(echo "$pytest_out" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")

partial_score=$(awk "BEGIN {printf \"%.4f\", $partial / $total}")
findings="${findings%,}"  # Remove trailing comma

cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {
    "partial_score": $partial_score,
    "checks_passed": $partial,
    "total_checks": $total,
    "pytest_passed": ${pytest_pass:-0},
    "pytest_failed": ${pytest_fail:-0}
  },
  "failure_modes": [],
  "checklist": [$findings]
}
EOF

# hermetic-by: scripts/make_graders_hermetic.py
