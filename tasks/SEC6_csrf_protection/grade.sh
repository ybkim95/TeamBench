#!/usr/bin/env bash
# Grade script for SEC6: CSRF Protection
# Usage: grade.sh <WORKSPACE> <REPORTS> <SUBMISSION> <TASK_DIR>
set -o pipefail
WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"

mkdir -p "$REPORTS"

CHECKS=0; PASSED=0; FAILURES=""
check() {
  local label="$2"
  CHECKS=$((CHECKS + 1))
  if eval "$1" 2>/dev/null; then
    PASSED=$((PASSED + 1))
  else
    FAILURES="${FAILURES:+${FAILURES},}${label}"
  fi
}

cd "$WORKSPACE"

# ── Check 1: CSRF token generated and stored in session ───────────────────────
check "python3 << 'PYEOF'
with open('app.py') as f:
    code = f.read()

# Must write a csrf-keyed value into session
has_session_write = ('session[' in code and 'csrf' in code.lower())
assert has_session_write, 'No CSRF token written to session in app.py'

# Must use secrets module for token generation
assert 'secrets' in code, 'secrets module not used'
assert ('token_hex' in code or 'token_bytes' in code or 'token_urlsafe' in code), \
    'No cryptographic token generation found'
print('CSRF_TOKEN_GENERATED_IN_SESSION')
PYEOF" "csrf_token_not_generated"

# ── Check 2: CSRF token embedded in HTML forms ────────────────────────────────
check "python3 << 'PYEOF'
import re
with open('app.py') as f:
    code = f.read()

# Must have an actual <input ... hidden ... csrf_token ...> tag (not just a comment)
# Strip comments first
lines = [l for l in code.splitlines() if not l.strip().startswith('#') and '<!--' not in l]
clean = '\n'.join(lines)
has_input_tag = bool(re.search(r'<input[^>]+type=[\"\'\\]?hidden[\"\'\\]?[^>]+name=[\"\'\\]?csrf_token', clean, re.IGNORECASE)) \
    or bool(re.search(r'<input[^>]+name=[\"\'\\]?csrf_token[^>]+type=[\"\'\\]?hidden', clean, re.IGNORECASE))
assert has_input_tag, 'No <input type=hidden name=csrf_token> found in form HTML (comments excluded)'
print('CSRF_TOKEN_IN_FORM')
PYEOF" "csrf_token_not_in_form"

# ── Check 3: Double-submit cookie set on form pages ───────────────────────────
check "python3 << 'PYEOF'
with open('app.py') as f:
    code = f.read()

has_set_cookie = 'set_cookie' in code and 'csrf' in code.lower()
has_make_response = 'make_response' in code and 'csrf' in code.lower()
assert has_set_cookie or has_make_response, \
    'Double-submit cookie not set (no set_cookie with csrf name found)'
print('DOUBLE_SUBMIT_COOKIE_SET')
PYEOF" "double_submit_cookie_missing"

# ── Check 4: Protected endpoints validate CSRF token ─────────────────────────
check "python3 << 'PYEOF'
with open('app.py') as f:
    code = f.read()

# Strip comment lines so TODO comments don't fool the check
non_comment = '\n'.join(
    l for l in code.splitlines()
    if not l.strip().startswith('#')
)

reads_form_token = ('csrf_token' in non_comment and
    ('request.form' in non_comment or 'form.get' in non_comment))
reads_header_token = ('csrf' in non_comment.lower() and
    'request.headers' in non_comment)
assert reads_form_token or reads_header_token, \
    'CSRF token not read from request.form or request.headers (excluding comments)'

# Session must be read (not just written) in validation context
assert 'session.get' in non_comment or 'session[' in non_comment, \
    'CSRF token not compared against session value'

# There must be a 403 return (not just in webhook)
assert '403' in non_comment, 'No 403 return for CSRF failure'
print('CSRF_VALIDATION_PRESENT')
PYEOF" "csrf_validation_missing"

# ── Check 5: compare_digest used for constant-time comparison ─────────────────
check "python3 << 'PYEOF'
with open('app.py') as f:
    code = f.read()

assert 'compare_digest' in code, \
    'secrets.compare_digest not used for timing-safe comparison'
print('COMPARE_DIGEST_USED')
PYEOF" "timing_safe_comparison_missing"

# ── Check 6: Protected endpoints return 403 on CSRF failure ──────────────────
check "python3 << 'PYEOF'
with open('app.py') as f:
    code = f.read()

assert '403' in code, 'No HTTP 403 response found for CSRF failures'
assert 'jsonify' in code and 'error' in code, \
    'No JSON error body returned on CSRF failure'
print('CSRF_FAILURE_RETURNS_403_JSON')
PYEOF" "csrf_failure_wrong_response"

# ── Check 7: Error body contains expected CSRF error message ──────────────────
REPORTS_PATH="$REPORTS"
check "python3 << PYEOF
import json, os

expected_path = os.path.join('${REPORTS_PATH}', 'expected.json')
with open('app.py') as f:
    code = f.read()

if os.path.exists(expected_path):
    with open(expected_path) as f:
        exp = json.load(f)
    expected_msg = exp.get('csrf_error_msg', '')
    assert expected_msg in code, f'Expected CSRF error message not in app.py: {expected_msg}'
else:
    # Fallback: just check error key present
    assert ('\"error\"' in code or \"'error'\" in code), 'error key not in response'

print('ERROR_BODY_KEY_OK')
PYEOF" "csrf_error_body_wrong"

# ── Check 8: Read-only GET endpoints exist and are preserved ──────────────────
check "python3 << 'PYEOF'
with open('app.py') as f:
    code = f.read()

import re
# Count routes that specify GET method or have no methods kwarg (default GET)
get_with_method = len(re.findall(r'methods=\[.GET.\]', code))
# Routes without methods= kwarg: @app.route('/path')\n or @app.route('/path', )\n
no_method_routes = len(re.findall(r'@app\.route\([^)]+\)\s*\n', code))
total_gets = get_with_method + no_method_routes

assert total_gets >= 2, f'Expected at least 2 GET routes, found {total_gets}'
print('GET_ROUTES_PRESERVED')
PYEOF" "get_routes_broken"

# ── Check 9: Webhook endpoint preserved with HMAC logic ───────────────────────
check "python3 << 'PYEOF'
with open('app.py') as f:
    code = f.read()

assert 'webhook' in code.lower(), 'Webhook route removed from app.py'
assert 'hmac' in code.lower(), 'HMAC validation removed from webhook endpoint'
assert 'compare_digest' in code, 'HMAC compare_digest check missing from webhook'
print('WEBHOOK_HMAC_PRESERVED')
PYEOF" "webhook_broken"

# ── Check 10: Syntax check — app.py parses cleanly ───────────────────────────
check "python3 << 'PYEOF'
import py_compile
py_compile.compile('app.py', doraise=True)
print('SYNTAX_OK')
PYEOF" "syntax_error"

# ── Check 11: All route functions still present (no routes deleted) ───────────
check "python3 << 'PYEOF'
import ast

with open('app.py') as f:
    source = f.read()

tree = ast.parse(source)
funcs = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}

# Must have at least 9 functions: 3 protected + 3 form pages + 3 exempt + helper
assert len(funcs) >= 9, f'Too few route functions remain: {funcs}'
print('ROUTES_INTACT')
PYEOF" "routes_deleted"

# ── Check 12: No dangerous constructs introduced ──────────────────────────────
check "python3 << 'PYEOF'
import re
with open('app.py') as f:
    code = f.read()

assert 'eval(' not in code, 'eval() introduced'
assert 'exec(' not in code, 'exec() introduced'
assert not re.search(r'^import subprocess', code, re.MULTILINE), 'subprocess imported'
print('NO_NEW_VULNS')
PYEOF" "new_vulnerability_introduced"

# ── Check 13: Attestation ─────────────────────────────────────────────────────
SUBMISSION_PATH="$SUBMISSION"
check "python3 << PYEOF
import json
with open('${SUBMISSION_PATH}/attestation.json') as f:
    att = json.load(f)
assert att.get('verdict') == 'pass'
print('ATTESTATION_OK')
PYEOF" "bad_attestation"

# ── Score output ──────────────────────────────────────────────────────────────
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
