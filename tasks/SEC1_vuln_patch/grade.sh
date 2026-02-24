#!/usr/bin/env bash
set -euo pipefail
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

# 1. No string formatting in SQL queries (parameterized)
check "python3 -c \"
with open('app/routes.py') as f:
    code = f.read()
# Should not have f-string SQL
assert 'f\\\"SELECT' not in code and \\\"f'SELECT\\\" not in code, 'SQL injection still present'
# Should have parameterized query (? placeholder)
assert '?' in code or 'parameterized' in code.lower() or ':name' in code, 'No parameterized query found'
print('SQL_INJECTION_FIXED')
\"" "sql_injection_present"

# 2. No unescaped output in templates
check "python3 -c \"
with open('app/templates/index.html') as f:
    code = f.read()
# user_input should be escaped
import re
# Find all {{ variable }} without |e filter
unescaped = re.findall(r'\{\{\s*user_input\s*\}\}', code)
assert len(unescaped) == 0, f'Unescaped user_input in index.html: {unescaped}'
print('XSS_FIXED')
\"" "xss_present"

# 3. No hardcoded secrets
check "python3 -c \"
with open('app/auth.py') as f:
    code = f.read()
assert 'sk-prod-' not in code, 'Hardcoded API key still present'
assert 'abc123' not in code, 'Hardcoded secret still present'
# Should use env var
assert 'os.environ' in code or 'os.getenv' in code or 'environ' in code, 'API key not from env var'
print('HARDCODED_SECRET_FIXED')
\"" "hardcoded_secret_present"

# 4. Path traversal mitigated
check "python3 -c \"
with open('app/routes.py') as f:
    code = f.read()
# Should have path validation
has_basename = 'os.path.basename' in code
has_secure = 'secure_filename' in code
has_realpath = 'os.path.realpath' in code or 'os.path.abspath' in code
has_check = '..' not in code or 'if' in code  # some form of validation
assert has_basename or has_secure or has_realpath, 'No path traversal mitigation found'
print('PATH_TRAVERSAL_FIXED')
\"" "path_traversal_present"

# 5. Session cookie secure = True
check "python3 -c \"
with open('app/auth.py') as f:
    code = f.read()
import re
assert re.search(r'SESSION_COOKIE_SECURE.*=.*True', code), 'Session cookie not secure'
print('SESSION_SECURE_FIXED')
\"" "insecure_session"

# 6. CSRF protection STILL WORKS
check "python3 -c \"
with open('app/utils.py') as f:
    code = f.read()
assert 'generate_csrf_token' in code, 'CSRF token generation removed'
assert 'validate_csrf_token' in code, 'CSRF token validation removed'
assert 'secrets' in code, 'CSRF still uses secrets module'
print('CSRF_PRESERVED')
\"" "csrf_protection_broken"

# 7. Profile template STILL properly escaped
check "python3 -c \"
with open('app/templates/profile.html') as f:
    code = f.read()
assert '|e' in code, 'Profile template escaping removed'
import re
assert re.search(r'\{\{[\s]*username[\s]*\|[\s]*e[\s]*\}\}', code), 'Profile escaping modified incorrectly'
print('PROFILE_PRESERVED')
\"" "profile_escaping_broken"

# 8. All Python files are syntactically valid
check "python3 -c \"
import py_compile, os
for root, dirs, files in os.walk('app'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            py_compile.compile(path, doraise=True)
print('SYNTAX_OK')
\"" "syntax_error"

# 9. All routes still accessible (basic import check)
check "python3 -c \"
import ast
with open('app/routes.py') as f:
    tree = ast.parse(f.read())
routes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name in ('index', 'profile', 'search', 'download')]
assert len(routes) == 4, f'Expected 4 route functions, got {len(routes)}'
print('ROUTES_OK')
\"" "routes_missing"

# 10. No new vulnerabilities introduced
check "python3 -c \"
with open('app/routes.py') as f:
    code = f.read()
assert 'eval(' not in code, 'eval() introduced'
assert 'exec(' not in code, 'exec() introduced'
assert 'subprocess' not in code or 'import subprocess' not in code, 'subprocess introduced'
print('NO_NEW_VULNS')
\"" "new_vulnerability_introduced"

# 11. Diff is reasonable (< 30 lines changed)
check "python3 -c \"
# Just verify the changes are minimal by checking file sizes are reasonable
import os
total_size = 0
for root, dirs, files in os.walk('app'):
    for f in files:
        total_size += os.path.getsize(os.path.join(root, f))
# Original is ~2500 bytes, shouldn't grow to more than 4000
assert total_size < 5000, f'Total code size too large: {total_size}'
print('DIFF_OK')
\"" "excessive_changes"

# 12. Attestation
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
