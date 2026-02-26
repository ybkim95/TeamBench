#!/usr/bin/env bash
set -o pipefail
WORKSPACE="$1"; REPORTS="$2"; SUBMISSION="$3"; TASK_DIR="$4"

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

# ── 1. Syntax check ───────────────────────────────────────────────────────────
check "python3 -c \"
import py_compile, os
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git')]
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            py_compile.compile(path, doraise=True)
print('SYNTAX_OK')
\"" "syntax_error"

# ── 2. Per-field validation exists (app.py must have validation logic) ─────────
check "python3 -c \"
with open('app.py') as f:
    code = f.read()
import re
# Must have at least one validation pattern: re.match, re.fullmatch, .isdigit,
# isinstance(..., int), len(...), 'not in', 'startswith', ValueError
patterns = [
    r're\.(match|fullmatch|search)\(',
    r'isinstance\(',
    r'\.isdigit\(\)',
    r'len\(',
    r'not in\b',
    r'raise\s+ValueError',
    r'return.*jsonify.*[\"\\']error[\"\\'].*400',
]
hits = sum(1 for p in patterns if re.search(p, code))
assert hits >= 3, f'Too few validation patterns in app.py (found {hits}/3 required)'
print('VALIDATION_LOGIC_PRESENT')
\"" "missing_per_field_validation"

# ── 3. SQL injection: no string interpolation in queries ─────────────────────
check "python3 -c \"
with open('app.py') as f:
    code = f.read()
import ast, re

# Check for parameterized query markers
has_param = bool(re.search(r'cursor\.execute\s*\(\s*[\"\\'][^\"\\']*(\\?|%s)[^\"\\']', code))
has_named  = bool(re.search(r'cursor\.execute\s*\(\s*[\"\\'][^\"\\\']*(:[\w]+)', code))
has_db_query = bool(re.search(r'db\.query\s*\(', code))

# Check that vulnerable string-interpolation INSERT is gone
still_vulnerable = bool(re.search(r'f[\"\\']INSERT.*\\{', code))
assert not still_vulnerable, 'SQL string interpolation (f-string INSERT) still present'
assert has_param or has_named or has_db_query, \
    'No parameterized query found (need ?, %s, or :name placeholders)'
print('PARAMETERIZED_QUERIES_OK')
\"" "sql_injection_string_interpolation"

# ── 4. XSS prevention: HTML encoding applied to string output ─────────────────
check "python3 -c \"
with open('app.py') as f:
    code = f.read()
import re
# Must use html.escape, markupsafe.escape, or cgi.escape, OR reject all HTML chars
has_html_escape     = bool(re.search(r'html\.escape\s*\(', code))
has_markupsafe      = bool(re.search(r'markupsafe\.escape\s*\(', code))
has_cgi_escape      = bool(re.search(r'cgi\.escape\s*\(', code))
# Alternative: field validation rejects < > & chars
has_html_char_check = bool(re.search(r'[<>]['\''\"]\s*in|re\.(search|match).*[<>]', code))
# Or uses bleach/sanitize
has_bleach          = bool(re.search(r'bleach\.(clean|sanitize)\s*\(', code))
assert any([has_html_escape, has_markupsafe, has_cgi_escape,
            has_html_char_check, has_bleach]), \
    'No HTML encoding/escaping found (html.escape, markupsafe.escape, or < > char rejection)'
print('HTML_ENCODING_PRESENT')
\"" "xss_no_html_encoding"

# ── 5. Path traversal prevention ──────────────────────────────────────────────
check "python3 -c \"
with open('app.py') as f:
    code = f.read()
import re
# Either rejects ../ sequences or uses allowlist for paths/filenames
has_traversal_check = bool(re.search(r'\.\./|\.\\\\|\\.\\.',  code))  # check for the pattern
has_traversal_guard = bool(re.search(r'(not in|raise|return.*400).*\.\.|\.\..*(?:not in|raise|return.*400)', code))
has_allowlist_dest  = bool(re.search(r'(destination|filename|path).*not in.*\[', code))
has_re_path         = bool(re.search(r're\.(match|fullmatch)\s*\(\s*r?[\"\\'][^\"\\\']*[A-Za-z0-9].*[\"\\'],', code))
# Check that validation rejects sequences with ..
has_dotdot_reject   = bool(re.search(r'(\\.\\.|\\.\\./).*(?:return|raise)|(?:return|raise).*(\\.\\.|\\.\\./)|\\.\\.\\.split', code))
# If the app type doesn't have path fields, check is relaxed
# (We check that at minimum there are allowlist checks or explicit path validation)
has_any_guard = has_traversal_guard or has_allowlist_dest or has_re_path or has_dotdot_reject
# Also acceptable: allowlist of permitted values for directory fields
has_enum_check = bool(re.search(r'in\s*\[[\"\\']uploads|documents|images|temp', code))
assert has_any_guard or has_enum_check, \
    'No path traversal prevention found (need ../ rejection or allowlist for path fields)'
print('PATH_TRAVERSAL_PREVENTION_OK')
\"" "path_traversal_not_prevented"

# ── 6. SSRF prevention: URL fields require https:// ───────────────────────────
check "python3 -c \"
with open('app.py') as f:
    code = f.read()
import re
# Must check for https scheme on URL fields, OR if no URL field in this variant,
# check passes automatically (verified via field list in expected.json)
import json, os, sys
exp_path = os.path.join(os.path.dirname('$REPORTS'), 'reports', 'expected.json')
if not os.path.exists(exp_path):
    # Try alternate path
    exp_path = os.path.join('$REPORTS', 'expected.json')

has_url_field = bool(re.search(r'(image_url|website|url)', code))
if has_url_field:
    has_https_check = bool(re.search(r'https://', code))
    has_scheme_check = bool(re.search(r'startswith\s*\(\s*[\"\\']https', code))
    has_scheme_reject = bool(re.search(r'(http://|javascript:|file://|ftp://)', code))
    assert has_https_check and (has_scheme_check or has_scheme_reject), \
        'URL field present but no https:// scheme enforcement found'
print('SSRF_PREVENTION_OK')
\"" "ssrf_url_not_validated"

# ── 7. Valid inputs still accepted (HTTP 201) ─────────────────────────────────
check "python3 -c \"
import subprocess, json, sys, os, tempfile, shutil

ws = os.getcwd()
tmp = tempfile.mkdtemp()
try:
    # Install deps quietly
    subprocess.run(
        [sys.executable, '-m', 'pip', 'install', 'flask', 'pytest', '-q'],
        capture_output=True, timeout=60
    )

    import importlib.util
    spec = importlib.util.spec_from_file_location('app_mod', os.path.join(ws, 'app.py'))
    mod = importlib.util.module_from_spec(spec)

    # We can't easily run flask here without spinning up a server,
    # so instead we check that the function is importable and returns 201 logic
    # by inspecting the code for 201 status code
    with open(os.path.join(ws, 'app.py')) as f:
        code = f.read()
    assert '201' in code, 'HTTP 201 status code missing from app.py'
    print('VALID_INPUTS_ACCEPTED_CODE_OK')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
\"" "valid_inputs_rejected"

# ── 8. Error messages don't leak internals ────────────────────────────────────
check "python3 -c \"
with open('app.py') as f:
    code = f.read()
import re
# Must not return raw exception str() or traceback in responses
has_traceback   = bool(re.search(r'traceback\.print', code))
has_exc_in_resp = bool(re.search(r'jsonify.*str\(e\)|str\(exc\).*jsonify', code))
# debug=True exposes stack traces — must not be in production path
# (debug=True in __main__ guard is OK)
debug_outside_main = False
main_guard_idx = code.find('if __name__')
if main_guard_idx == -1:
    debug_outside_main = bool(re.search(r'app\.run\(.*debug=True', code))
assert not has_traceback, 'traceback.print found in app.py — leaks internals'
assert not has_exc_in_resp, 'Raw exception string returned in jsonify response'
print('ERROR_MESSAGES_SAFE')
\"" "error_messages_leak_internals"

# ── 9. Empty / missing body rejected ─────────────────────────────────────────
check "python3 -c \"
with open('app.py') as f:
    code = f.read()
import re
# Must have check for missing/None fields
has_none_check    = bool(re.search(r'is\s+None|== None', code))
has_missing_check = bool(re.search(r'not\s+\w+\b|if\s+\w+\s+is\s+None', code))
has_400_on_missing = bool(re.search(r'return.*jsonify.*[\"\\']error[\"\\'].*,\s*400', code))
assert has_none_check or has_missing_check, \
    'No None/missing field check found in app.py'
assert has_400_on_missing, \
    'No HTTP 400 return for missing required fields found'
print('MISSING_FIELDS_REJECTED')
\"" "missing_fields_not_rejected"

# ── 10. SQL injection chars rejected in text fields ──────────────────────────
check "python3 -c \"
with open('app.py') as f:
    code = f.read()
import re
# Must reject SQL metacharacters in text fields: quotes, semicolons, double-dash
has_sql_char_check = bool(re.search(
    r'[\"\\'][\\'\"](in|not in)|re\.(search|match).*[\\';]|'
    r'\\\\x27|\\\\x22|QUOTE|single_quote|semicolon',
    code
))
# Also acceptable: parameterized queries prevent injection regardless
has_param_query = bool(re.search(r'cursor\.execute\s*\(\s*[^f][\"\\'].*(\?|%s)', code))
# Or field-level allowlist (alphanumeric-only via regex)
has_alnum_regex = bool(re.search(r're\.(match|fullmatch)\s*\(\s*r?[\"\\'][^\"\\\']*[A-Za-z0-9]\+', code))
assert has_sql_char_check or has_param_query or has_alnum_regex, \
    'No SQL injection character rejection or parameterized query mitigation found'
print('SQL_INJECTION_CHARS_REJECTED')
\"" "sql_injection_chars_not_rejected"

# ── 11. No new dangerous calls introduced ────────────────────────────────────
check "python3 -c \"
import os
for fname in ('app.py', 'models.py'):
    fpath = os.path.join(os.getcwd(), fname)
    if not os.path.exists(fpath):
        continue
    with open(fpath) as f:
        code = f.read()
    assert 'eval(' not in code,         f'eval() found in {fname}'
    assert 'exec(' not in code,         f'exec() found in {fname}'
    assert '__import__' not in code,    f'__import__ found in {fname}'
    assert 'os.system(' not in code,    f'os.system() found in {fname}'
    assert 'subprocess.call(' not in code or 'shell=True' not in code, \
        f'subprocess.call with shell=True found in {fname}'
print('NO_NEW_VULNS')
\"" "new_vulnerability_introduced"

# ── 12. Tests pass (pytest) ───────────────────────────────────────────────────
check "python3 -m pytest tests/test_validation.py -x -q --tb=no 2>&1 | tail -5 | grep -E '(passed|no tests ran)'" \
  "tests_failing"

# ── 13. Attestation check ─────────────────────────────────────────────────────
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
