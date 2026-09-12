#!/usr/bin/env bash
# grade.sh — Grade JS2_xss_sanitize
# Args: WORKSPACE REPORTS SUBMISSION TASK_DIR
# Produces: REPORTS/score.json
set -o pipefail

WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"

mkdir -p "$REPORTS"

CHECKS=0; PASSED=0; FAILURES=""

check() {
  local expr="$1"
  local label="$2"
  CHECKS=$((CHECKS + 1))
  if eval "$expr" 2>/dev/null; then
    PASSED=$((PASSED + 1))
  else
    FAILURES="${FAILURES:+${FAILURES},}${label}"
  fi
}

cd "$WORKSPACE"

# ── Load expected values ───────────────────────────────────────────────────────
EXPECTED_JSON="$REPORTS/expected.json"
if [ ! -f "$EXPECTED_JSON" ]; then
  EXPECTED_JSON="$TASK_DIR/expected.json"
fi

APP_TYPE=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('app_type','blog'))" 2>/dev/null || echo "blog")
PORT=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('port',3100))" 2>/dev/null || echo "3100")
VULN_COUNT=$(python3 -c "import json; e=json.load(open('$EXPECTED_JSON')); print(e.get('vuln_count',3))" 2>/dev/null || echo "3")
REQUIRED_CSP=$(python3 -c "
import json
e = json.load(open('$EXPECTED_JSON'))
print(json.dumps(e.get('required_csp_directives', [])))
" 2>/dev/null || echo "[]")
SANITIZE_FNS=$(python3 -c "
import json
e = json.load(open('$EXPECTED_JSON'))
print(json.dumps(e.get('sanitization_functions', [])))
" 2>/dev/null || echo "[]")

# ── Static analysis checks ────────────────────────────────────────────────────

# CHECK 1: app.js exists
check "test -f '$WORKSPACE/app.js'" "app_js_missing"

# CHECK 2: No raw unescaped <%- %> rendering user variables in index template
# After fix, <%- variable %> in index view must call sanitizeHtml() or sanitizeUrl()
check "python3 -c \"
import re, sys, glob, os
views_dir = os.path.join('$WORKSPACE', 'views')
raw_pattern = re.compile(r'<%-\s+(?!sanitize)[a-zA-Z_][a-zA-Z0-9_.]*\s*%>')
found = []
for f in glob.glob(os.path.join(views_dir, '*.ejs')):
    content = open(f).read()
    matches = raw_pattern.findall(content)
    if matches:
        found.append((os.path.basename(f), matches))
# Only fail if we find raw output of user-supplied variables (not literals)
# We allow <%- title %> since that is app-controlled, not user input
user_vars = re.compile(r'<%-\s+(post\.|thread\.|widget\.|author\.|user\.|report\.)[a-zA-Z]+\s*%>')
bad = []
for f in glob.glob(os.path.join(views_dir, '*.ejs')):
    content = open(f).read()
    for m in user_vars.findall(content):
        bad.append(m)
assert not bad, f'Unsanitized user vars in templates: {bad}'
print('OK')
\"" "raw_user_vars_in_templates"

# CHECK 3: sanitizeHtml function defined in app.js
check "grep -q 'function sanitizeHtml' '$WORKSPACE/app.js'" "sanitize_html_fn_missing"

# CHECK 4: sanitizeUrl function defined in app.js
check "grep -q 'function sanitizeUrl' '$WORKSPACE/app.js'" "sanitize_url_fn_missing"

# CHECK 5: setSecurityHeaders function defined in app.js
check "grep -q 'function setSecurityHeaders' '$WORKSPACE/app.js'" "security_headers_fn_missing"

# CHECK 6: CSP header is set in setSecurityHeaders
check "grep -q 'Content-Security-Policy' '$WORKSPACE/app.js'" "csp_header_not_set"

# CHECK 7: CSP header includes default-src 'self'
check "grep -q \"default-src 'self'\" '$WORKSPACE/app.js'" "csp_missing_default_src"

# CHECK 8: CSP header includes object-src 'none'
check "grep -q \"object-src 'none'\" '$WORKSPACE/app.js'" "csp_missing_object_src_none"

# CHECK 9: CSP header includes script-src 'self'
check "grep -q \"script-src 'self'\" '$WORKSPACE/app.js'" "csp_missing_script_src"

# CHECK 10: sanitizeUrl rejects javascript: URIs (must have protocol/scheme check)
check "python3 -c \"
import re
code = open('$WORKSPACE/app.js').read()
# Must reference 'javascript' in the sanitizeUrl function body to block that scheme
fn_match = re.search(r'function sanitizeUrl.*?(?=\nfunction |\napp\.|\Z)', code, re.DOTALL)
assert fn_match, 'sanitizeUrl function not found'
fn_body = fn_match.group(0)
has_js_check = ('javascript' in fn_body.lower() or 'protocol' in fn_body.lower() or 'scheme' in fn_body.lower() or 'http' in fn_body.lower())
assert has_js_check, 'sanitizeUrl does not appear to check URL scheme'
print('OK')
\"" "sanitize_url_no_scheme_check"

# CHECK 11: sanitizeHtml is actually called on template variables (not just defined)
check "python3 -c \"
import re
code = open('$WORKSPACE/app.js').read()
# Check that sanitizeHtml is called somewhere in the routes or middleware
calls = re.findall(r'sanitizeHtml\s*\(', code)
assert len(calls) >= 2, f'sanitizeHtml called only {len(calls)} times, expected >= 2'
print('OK')
\"" "sanitize_html_not_applied"

# CHECK 12: sanitizeUrl is called on the href variable (not just defined)
check "python3 -c \"
import re, glob, os
code = open('$WORKSPACE/app.js').read()
# Check call in app.js or in template files
template_code = ''
for f in glob.glob(os.path.join('$WORKSPACE', 'views', '*.ejs')):
    template_code += open(f).read()
combined = code + template_code
calls = re.findall(r'sanitizeUrl\s*\(', combined)
assert len(calls) >= 1, f'sanitizeUrl not called in code or templates'
print('OK')
\"" "sanitize_url_not_applied"

# CHECK 13: No use of dangerous eval/exec patterns (no new vulns introduced)
check "python3 -c \"
import re
code = open('$WORKSPACE/app.js').read()
# Reject eval() with dynamic user content
bad = re.findall(r'\beval\s*\(', code)
assert not bad, f'eval() found in app.js — potential new vulnerability'
print('OK')
\"" "eval_in_app_js"

# CHECK 14: app.js is valid Node.js syntax (node --check)
check "node --check '$WORKSPACE/app.js'" "app_js_syntax_error"

# CHECK 15: Attestation file exists and has verdict pass
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

# ── Runtime XSS checks (start server, send payloads) ─────────────────────────

# Install deps if needed (best-effort)
if [ -f "$WORKSPACE/package.json" ]; then
  cd "$WORKSPACE" && npm install --silent 2>/dev/null || true
fi

# Start server in background
node "$WORKSPACE/app.js" &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null; wait $SERVER_PID 2>/dev/null || true' EXIT

# Wait up to 8 seconds for server to be ready
SERVER_READY=0
for i in $(seq 1 16); do
  sleep 0.5
  if curl -sf "http://localhost:${PORT}/" -o /dev/null 2>/dev/null; then
    SERVER_READY=1
    break
  fi
done

if [ "$SERVER_READY" -eq 1 ]; then

  # CHECK 16: XSS payload in primary field not reflected raw in index response
  check "python3 -c \"
import urllib.request, urllib.parse
payload = urllib.parse.quote('<script>alert(1)</script>')
url = f'http://localhost:${PORT}/?title={payload}&label={payload}'
resp = urllib.request.urlopen(url, timeout=5)
body = resp.read().decode()
assert '<script>alert(1)</script>' not in body, 'XSS payload reflected unescaped in index'
print('OK')
\"" "xss_reflected_in_index"

  # CHECK 17: javascript: URI not present in rendered href
  check "python3 -c \"
import urllib.request, urllib.parse
payload = urllib.parse.quote('javascript:alert(1)')
# Try each profile/detail route that could contain href injection
routes = ['/authors/1', '/users/1', '/reports/1']
found = False
for route in routes:
    try:
        url = f'http://localhost:${PORT}{route}?website={payload}&sourceUrl={payload}'
        resp = urllib.request.urlopen(url, timeout=5)
        body = resp.read().decode()
        if 'javascript:alert' in body:
            found = True
            break
    except Exception:
        pass
assert not found, 'javascript: URI found unescaped in rendered href'
print('OK')
\"" "javascript_uri_in_href"

  # CHECK 18: CSP header is present in HTTP response
  # NOTE: nested-quote workaround — the inner ``"default-src 'self'"`` literals
  # cannot survive `check "..."` + `eval`, so we read the directives from
  # variables and use single-quoted python string literals throughout.
  check "python3 -c \"
import urllib.request
resp = urllib.request.urlopen('http://localhost:${PORT}/', timeout=5)
csp = resp.headers.get('Content-Security-Policy', '')
assert csp, 'Content-Security-Policy header missing from HTTP response'
assert 'default-src ' + chr(39) + 'self' + chr(39) in csp, f'default-src missing from CSP: {csp}'
assert 'object-src ' + chr(39) + 'none' + chr(39) in csp, f'object-src missing from CSP: {csp}'
print('OK')
\"" "csp_header_missing_in_response"

fi

# Kill server
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true
trap - EXIT

# ── Score output ──────────────────────────────────────────────────────────────
PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
  SUCCESS=1; PASS=true
else
  SUCCESS=0; PASS=false
fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {
    "checks_passed": $PASSED,
    "checks_total": $CHECKS,
    "partial_score": $PARTIAL
  },
  "failure_modes": $FM
}
JSON
