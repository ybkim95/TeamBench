#!/usr/bin/env bash
# CROSS4 grader: verify 5 security bugs are fixed in the auth federation gateway
set -euo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"
SUBMISSION="${3:-/submission}"
TASK_DIR="${4:-/task}"

cd "$WORKSPACE"

pass=true
partial=0
total=14
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
pip install PyJWT cryptography pytest 2>/dev/null | tail -1 || true

# -------------------------------------------------------------------
# C1: Syntax validity — gateway/auth.py and gateway/rbac.py parse OK
# -------------------------------------------------------------------
if python3 -c "
import ast, sys
for f in ['gateway/auth.py', 'gateway/rbac.py']:
    try:
        ast.parse(open(f).read())
    except SyntaxError as e:
        print(f'Syntax error in {f}: {e}', file=sys.stderr)
        sys.exit(1)
sys.exit(0)
" 2>/dev/null; then
    check "C1" "Syntax valid: gateway/auth.py and gateway/rbac.py parse cleanly" "pass"
else
    check "C1" "Syntax error in gateway/auth.py or gateway/rbac.py" "fail"
fi

# -------------------------------------------------------------------
# C2: Both services still import correctly
# -------------------------------------------------------------------
if python3 -c "
import importlib.util, sys

def try_import(path, name):
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as e:
        print(f'Import failed for {path}: {e}', file=sys.stderr)
        sys.exit(1)

try_import('gateway/auth.py', 'gateway_auth')
try_import('gateway/rbac.py', 'gateway_rbac')
sys.exit(0)
" 2>/dev/null; then
    check "C2" "Both gateway modules import without errors" "pass"
else
    check "C2" "gateway/auth.py or gateway/rbac.py fails to import" "fail"
fi

# -------------------------------------------------------------------
# C3: Bug 1 fixed — JWT rejects HS256 (static check: only RS256 in algorithms list)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('gateway/auth.py').read()
tree = ast.parse(src)

# Find all Call nodes with keywords containing 'algorithms'
found_rs256_only = False
found_hs256 = False

for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        for kw in node.keywords:
            if kw.arg == 'algorithms':
                # Must be a list literal
                if isinstance(kw.value, ast.List):
                    elts = [e.s if isinstance(e, ast.Constant) else '' for e in kw.value.elts]
                    if 'HS256' in elts:
                        found_hs256 = True
                    if elts == ['RS256']:
                        found_rs256_only = True

if found_hs256:
    print('FAIL: HS256 still in algorithms list', file=sys.stderr)
    sys.exit(1)
if not found_rs256_only:
    print('FAIL: RS256-only algorithms list not found', file=sys.stderr)
    sys.exit(1)
sys.exit(0)
PYEOF
then
    check "C3" "Bug 1 fixed: algorithms=[RS256] only — HS256 rejected" "pass"
else
    check "C3" "Bug 1 not fixed: HS256 still accepted or RS256-only not enforced in auth.py" "fail"
fi

# -------------------------------------------------------------------
# C4: Bug 2 fixed — hmac.compare_digest used for API key comparison
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('gateway/auth.py').read()
tree = ast.parse(src)

found_compare_digest = False
for node in ast.walk(tree):
    if isinstance(node, ast.Attribute):
        if node.attr == 'compare_digest':
            found_compare_digest = True
            break
    # Also accept direct call: compare_digest(...)
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == 'compare_digest':
            found_compare_digest = True
            break

if not found_compare_digest:
    print('FAIL: hmac.compare_digest not found in auth.py', file=sys.stderr)
    sys.exit(1)
sys.exit(0)
PYEOF
then
    check "C4" "Bug 2 fixed: hmac.compare_digest used for API key comparison" "pass"
else
    check "C4" "Bug 2 not fixed: hmac.compare_digest not found in gateway/auth.py" "fail"
fi

# -------------------------------------------------------------------
# C5: Bug 3 fixed — role mapping includes admin -> superuser
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('gateway/rbac.py').read()
tree = ast.parse(src)

# Look for a dict literal containing "admin" -> "superuser"
found = False
for node in ast.walk(tree):
    if isinstance(node, ast.Dict):
        for k, v in zip(node.keys, node.values):
            if (isinstance(k, ast.Constant) and k.value == 'admin' and
                    isinstance(v, ast.Constant) and v.value == 'superuser'):
                found = True
                break

if not found:
    print('FAIL: "admin": "superuser" not in ROLE_MAP', file=sys.stderr)
    sys.exit(1)
sys.exit(0)
PYEOF
then
    check "C5" "Bug 3 fixed: role mapping includes admin -> superuser" "pass"
else
    check "C5" "Bug 3 not fixed: admin -> superuser mapping missing in gateway/rbac.py" "fail"
fi

# -------------------------------------------------------------------
# C6: Bug 4 fixed — session token expiry > 0 (static check)
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('gateway/auth.py').read()
tree = ast.parse(src)

# Find exp assignment in create_session_token or similar; check not literal 0
# Look for dict with "exp" key set to 0 constant
exp_is_zero = False
for node in ast.walk(tree):
    if isinstance(node, ast.Dict):
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and k.value == 'exp':
                if isinstance(v, ast.Constant) and v.value == 0:
                    exp_is_zero = True

# Also check for exp = 0 assignment
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == 'exp':
                if isinstance(node.value, ast.Constant) and node.value.value == 0:
                    exp_is_zero = True

if exp_is_zero:
    print('FAIL: exp still set to literal 0', file=sys.stderr)
    sys.exit(1)

# Also verify time.time() or similar is used for exp
found_time_based = False
for node in ast.walk(tree):
    if isinstance(node, ast.Dict):
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and k.value == 'exp':
                src_val = ast.unparse(v)
                if 'time' in src_val or '3600' in src_val:
                    found_time_based = True

if not found_time_based:
    print('FAIL: exp not set using time-based expression + 3600', file=sys.stderr)
    sys.exit(1)
sys.exit(0)
PYEOF
then
    check "C6" "Bug 4 fixed: session token expiry set to time.time() + 3600" "pass"
else
    check "C6" "Bug 4 not fixed: session exp still 0 or not time-based in gateway/auth.py" "fail"
fi

# -------------------------------------------------------------------
# C7: Bug 5 fixed — audience validation present in validate_jwt()
# -------------------------------------------------------------------
if python3 - <<'PYEOF' 2>/dev/null
import ast, sys

src = open('gateway/auth.py').read()
tree = ast.parse(src)

found_audience = False
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        for kw in node.keywords:
            if kw.arg == 'audience':
                # Must not be None
                if not (isinstance(kw.value, ast.Constant) and kw.value.value is None):
                    found_audience = True

if not found_audience:
    print('FAIL: audience= parameter not set in jwt.decode call', file=sys.stderr)
    sys.exit(1)
sys.exit(0)
PYEOF
then
    check "C7" "Bug 5 fixed: audience validation present in validate_jwt()" "pass"
else
    check "C7" "Bug 5 not fixed: audience= None or missing in gateway/auth.py jwt.decode" "fail"
fi

# -------------------------------------------------------------------
# C8: test_jwt_auth.py passes (includes RS256 signing test)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_jwt_auth.py -q --tb=short 2>/dev/null | grep -q "passed"; then
    check "C8" "test_jwt_auth.py: all JWT auth tests pass" "pass"
else
    check "C8" "test_jwt_auth.py: one or more JWT auth tests fail" "fail"
fi

# -------------------------------------------------------------------
# C9: test_apikey_auth.py passes
# -------------------------------------------------------------------
if python3 -m pytest tests/test_apikey_auth.py -q --tb=short 2>/dev/null | grep -q "passed"; then
    check "C9" "test_apikey_auth.py: all API key auth tests pass" "pass"
else
    check "C9" "test_apikey_auth.py: one or more API key auth tests fail" "fail"
fi

# -------------------------------------------------------------------
# C10: test_rbac.py passes (role mapping tests)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_rbac.py -q --tb=short 2>/dev/null | grep -q "passed"; then
    check "C10" "test_rbac.py: all role mapping tests pass" "pass"
else
    check "C10" "test_rbac.py: one or more role mapping tests fail" "fail"
fi

# -------------------------------------------------------------------
# C11: test_session.py passes (session expiry tests)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_session.py -q --tb=short 2>/dev/null | grep -q "passed"; then
    check "C11" "test_session.py: all session expiry tests pass" "pass"
else
    check "C11" "test_session.py: one or more session expiry tests fail" "fail"
fi

# -------------------------------------------------------------------
# C12: test_federation.py passes (end-to-end federation tests)
# -------------------------------------------------------------------
if python3 -m pytest tests/test_federation.py -q --tb=short 2>/dev/null | grep -q "passed"; then
    check "C12" "test_federation.py: all federation tests pass" "pass"
else
    check "C12" "test_federation.py: one or more federation tests fail" "fail"
fi

# -------------------------------------------------------------------
# C13: attack_vectors.py tests all pass (attacks are blocked after fixes)
# -------------------------------------------------------------------
if python3 -m pytest tests/attack_vectors.py -q --tb=short 2>/dev/null | grep -q "passed"; then
    check "C13" "attack_vectors.py: all attack tests pass (attacks are blocked)" "pass"
else
    check "C13" "attack_vectors.py: attack tests fail (attacks not fully blocked)" "fail"
fi

# -------------------------------------------------------------------
# C14: Full pytest suite passes
# -------------------------------------------------------------------
pytest_out=$(python3 -m pytest tests/ -q --tb=no 2>&1 || true)
pytest_pass=$(echo "$pytest_out" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
pytest_fail=$(echo "$pytest_out" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")

if [ "${pytest_fail:-0}" = "0" ] && [ "${pytest_pass:-0}" != "0" ]; then
    check "C14" "Full pytest suite: all tests pass (${pytest_pass} passed, 0 failed)" "pass"
else
    check "C14" "Full pytest suite: ${pytest_fail} test(s) failed" "fail"
fi

# -------------------------------------------------------------------
# Write score.json
# -------------------------------------------------------------------
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
