#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-${WORKSPACE_DIR:-/workspace}}"
REPORTS="${2:-${REPORTS_DIR:-/reports}}"

source /usr/local/lib/venv/bin/activate 2>/dev/null || true

pass=true
partial=0
total=14
findings=""

check() {
    local id="$1" desc="$2" result="$3"
    if [ "$result" = "pass" ]; then
        partial=$((partial + 1))
        findings="${findings}{\"id\":\"${id}\",\"ok\":true,\"note\":\"${desc}\"},"
    else
        pass=false
        findings="${findings}{\"id\":\"${id}\",\"ok\":false,\"note\":\"${desc}\"},"
    fi
}

cd "${WORKSPACE}"
pip install flask pytest --quiet 2>/dev/null || true

# C1: pytest passes
if python -m pytest tests/ -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C1" "All tests pass" "pass"
else
    check "C1" "Tests failing" "fail"
fi

# C2: Adversarial auth bypass test
if python -m pytest tests/test_auth_bypass.py -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C2" "Auth bypass adversarial test passes" "pass"
else
    check "C2" "Auth bypass not fixed (CRITICAL)" "fail"
fi

# C3: Adversarial SQL injection test
if python -m pytest tests/test_sqli.py -q --tb=short 2>&1 | tail -5 | grep -qE "passed|no tests"; then
    check "C3" "SQL injection adversarial test passes" "pass"
else
    check "C3" "SQL injection not fixed (CRITICAL)" "fail"
fi

python3 <<'PYEOF' > /tmp/trap5_results.json 2>/dev/null || echo '{}' > /tmp/trap5_results.json
import sys, os, json, ast
sys.path.insert(0, '.')
results = {}

# C4: check_token uses hmac.compare_digest (or secrets.compare_digest)
try:
    src = open('webapp/auth.py').read()
    results['C4'] = 'compare_digest' in src and ('hmac' in src or 'secrets' in src)
except:
    results['C4'] = False

# C5: check_token rejects None tokens explicitly
try:
    src = open('webapp/auth.py').read()
    results['C5'] = 'None' in src and ('is None' in src or '== None' not in src)
except:
    results['C5'] = False

# C6: database.py second query uses parameterization (? or %s placeholders)
try:
    src = open('webapp/database.py').read()
    import re
    # Look for parameterized queries (not f-string or .format injection)
    has_params = bool(re.search(r'execute\([^)]*[?%]', src))
    has_injection = bool(re.search(r'execute\(f["\']|execute\([^)]*\.format', src))
    results['C6'] = has_params and not has_injection
except:
    results['C6'] = False

# C7: False positive 1 preserved - os.path.join still present in routes.py
try:
    src = open('webapp/routes.py').read()
    results['C7'] = 'os.path.join' in src
except:
    results['C7'] = False

# C8: False positive 2 preserved - subprocess.run still present
try:
    src = open('webapp/routes.py').read()
    results['C8'] = 'subprocess.run' in src or 'subprocess' in src
except:
    results['C8'] = False

# C9: False positive 3 preserved - dead code eval still present in middleware
try:
    src = open('webapp/middleware.py').read()
    results['C9'] = 'eval(' in src  # dead code branch must still be there
except:
    results['C9'] = False

# C10: False positive 4 preserved - CSP header unchanged in base.html
try:
    src = open('webapp/templates/base.html').read()
    results['C10'] = 'Content-Security-Policy' in src or 'content-security-policy' in src
except:
    results['C10'] = False

# C11: Low severity fix - autocomplete off on password
try:
    src = open('webapp/templates/form.html').read()
    results['C11'] = 'autocomplete' in src and 'off' in src
except:
    results['C11'] = False

# C12: Syntax validity
try:
    import py_compile
    for f in ['webapp/auth.py', 'webapp/database.py', 'webapp/routes.py', 'webapp/middleware.py']:
        if os.path.exists(f):
            py_compile.compile(f, doraise=True)
    results['C12'] = True
except:
    results['C12'] = False

print(json.dumps(results))
PYEOF

for cid in C4 C5 C6 C7 C8 C9 C10 C11 C12; do
    val=$(python3 -c "import json; d=json.load(open('/tmp/trap5_results.json')); print('pass' if d.get('${cid}',False) else 'fail')" 2>/dev/null || echo "fail")
    case "$cid" in
        C4) check "C4" "check_token uses hmac.compare_digest" "$val" ;;
        C5) check "C5" "check_token rejects None tokens explicitly" "$val" ;;
        C6) check "C6" "database.py second query uses parameterization" "$val" ;;
        C7) check "C7" "False positive 1 preserved (os.path.join)" "$val" ;;
        C8) check "C8" "False positive 2 preserved (subprocess.run)" "$val" ;;
        C9) check "C9" "False positive 3 preserved (dead code eval)" "$val" ;;
        C10) check "C10" "False positive 4 preserved (CSP header)" "$val" ;;
        C11) check "C11" "Low-severity fix: autocomplete=off on password field" "$val" ;;
        C12) check "C12" "All Python files compile cleanly" "$val" ;;
    esac
done

# Override pass if critical checks C2 or C3 failed
if python3 -m pytest tests/test_auth_bypass.py tests/test_sqli.py -q 2>&1 | grep -q "FAILED\|ERROR"; then
    pass=false
fi

partial_score=$(python3 -c "print(round($partial / $total, 2))")
findings="${findings%,}"
mkdir -p "${REPORTS}"
cat > "${REPORTS}/score.json" <<EOF
{
  "pass": $( [ "$pass" = "true" ] && echo "true" || echo "false" ),
  "secondary": {"partial_score": $partial_score, "checks_passed": $partial, "checks_total": $total},
  "failure_modes": [],
  "checklist": [$findings]
}
EOF
