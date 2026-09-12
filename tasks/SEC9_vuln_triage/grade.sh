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

# Load expected for seed-specific params
APP_NAME=$(python3 -c "import json; print(json.load(open('$REPORTS/expected.json')).get('app_name', 'webapp'))" 2>/dev/null || echo "webapp")

# ── REAL VULNERABILITIES FIXED (5 checks) ───────────────────────────────────

# VULN-01: SQL Injection fixed
check "python3 -c \"
with open('app/routes.py') as f:
    content = f.read()
# The lookup_user function should use parameterized query
import re
# Find lookup_user function
fn_match = re.search(r'def lookup_user.*?(?=\ndef |\Z)', content, re.DOTALL)
if fn_match:
    fn_body = fn_match.group()
    # Should NOT have f-string or .format in SQL
    has_injection = ('f\"SELECT' in fn_body or 'f\\\"SELECT' in fn_body or
                     '\".format(' in fn_body or \"% (\" in fn_body)
    has_param = ('?' in fn_body or '%s' in fn_body)
    assert not has_injection or has_param, 'SQL injection in lookup_user not fixed'
else:
    assert False, 'lookup_user function not found'
print('VULN01_FIXED')
\"" "vuln01_sql_injection_not_fixed"

# VULN-02: Path Traversal fixed
check "python3 -c \"
with open('app/routes.py') as f:
    content = f.read()
import re
fn_match = re.search(r'def download_file.*?(?=\ndef |\Z)', content, re.DOTALL)
if fn_match:
    fn_body = fn_match.group()
    has_fix = ('realpath' in fn_body or 'abspath' in fn_body or
               'secure_filename' in fn_body or 'startswith' in fn_body or
               '..' in fn_body and 'reject' in fn_body.lower() or
               'os.path.commonpath' in fn_body or 'resolve()' in fn_body)
    assert has_fix, 'Path traversal in download_file not fixed'
else:
    assert False, 'download_file function not found'
print('VULN02_FIXED')
\"" "vuln02_path_traversal_not_fixed"

# VULN-03: SSRF fixed
check "python3 -c \"
with open('app/routes.py') as f:
    content = f.read()
import re
fn_match = re.search(r'def proxy_webhook.*?(?=\ndef |\Z)', content, re.DOTALL)
if fn_match:
    fn_body = fn_match.group()
    has_fix = ('127.0.0.1' in fn_body or 'localhost' in fn_body or
               'private' in fn_body.lower() or 'internal' in fn_body.lower() or
               '10.' in fn_body or '192.168' in fn_body or
               'ipaddress' in fn_body or 'urlparse' in fn_body or
               'blocked' in fn_body.lower() or 'allowlist' in fn_body.lower() or
               'whitelist' in fn_body.lower())
    assert has_fix, 'SSRF in proxy_webhook not fixed'
else:
    assert False, 'proxy_webhook function not found'
print('VULN03_FIXED')
\"" "vuln03_ssrf_not_fixed"

# VULN-04: Insecure Deserialization fixed
check "python3 -c \"
with open('app/routes.py') as f:
    content = f.read()
import re
fn_match = re.search(r'def import_config.*?(?=\ndef |\Z)', content, re.DOTALL)
if fn_match:
    fn_body = fn_match.group()
    has_pickle = 'pickle.loads' in fn_body or 'pickle.load(' in fn_body
    has_safe = 'json.loads' in fn_body or 'json.load(' in fn_body or 'yaml.safe_load' in fn_body
    assert not has_pickle or has_safe, 'Insecure deserialization in import_config not fixed'
else:
    assert False, 'import_config function not found'
print('VULN04_FIXED')
\"" "vuln04_deserialization_not_fixed"

# VULN-05: Hardcoded Secret Key fixed
check "python3 -c \"
with open('app/config.py') as f:
    content = f.read()
# Should use os.environ or os.getenv, not a hardcoded string
has_env = 'os.environ' in content or 'os.getenv' in content or 'environ' in content
# The old hardcoded pattern should be gone
import re
hardcoded = re.search(r'SECRET_KEY\s*=\s*[\x22\x27][a-zA-Z0-9_-]+[\x22\x27]', content)
if hardcoded:
    # Acceptable if it's a fallback in os.getenv('...', 'fallback')
    line = hardcoded.group()
    assert has_env, f'SECRET_KEY still hardcoded: {line}'
print('VULN05_FIXED')
\"" "vuln05_hardcoded_secret_not_fixed"

# ── MITIGATED FINDINGS PRESERVED (5 checks) ─────────────────────────────────

# MIT-01: CSRF middleware preserved
check "python3 -c \"
import os
assert os.path.exists('middleware/csrf_middleware.py'), 'CSRF middleware file deleted'
with open('middleware/csrf_middleware.py') as f:
    content = f.read()
assert 'csrf' in content.lower() and 'validate' in content.lower(), 'CSRF middleware gutted'
assert len(content) > 100, 'CSRF middleware appears emptied'
print('MIT01_PRESERVED')
\"" "mit01_csrf_middleware_broken"

# MIT-02: Rate limiter preserved
check "python3 -c \"
import os
assert os.path.exists('middleware/rate_limiter.py'), 'Rate limiter file deleted'
with open('middleware/rate_limiter.py') as f:
    content = f.read()
assert 'rate' in content.lower() or 'limit' in content.lower(), 'Rate limiter gutted'
assert len(content) > 100, 'Rate limiter appears emptied'
print('MIT02_PRESERVED')
\"" "mit02_rate_limiter_broken"

# MIT-03: Sanitizer preserved
check "python3 -c \"
import os
assert os.path.exists('middleware/sanitizer.py'), 'Sanitizer file deleted'
with open('middleware/sanitizer.py') as f:
    content = f.read()
assert 'sanitiz' in content.lower() or 'escape' in content.lower() or 'strip' in content.lower(), 'Sanitizer gutted'
assert len(content) > 80, 'Sanitizer appears emptied'
print('MIT03_PRESERVED')
\"" "mit03_sanitizer_broken"

# MIT-04: Upload middleware preserved
check "python3 -c \"
import os
assert os.path.exists('middleware/upload_middleware.py'), 'Upload middleware file deleted'
with open('middleware/upload_middleware.py') as f:
    content = f.read()
assert 'mime' in content.lower() or 'content_type' in content.lower() or 'upload' in content.lower(), 'Upload middleware gutted'
print('MIT04_PRESERVED')
\"" "mit04_upload_middleware_broken"

# MIT-05: Session middleware preserved
check "python3 -c \"
import os
assert os.path.exists('middleware/session_middleware.py'), 'Session middleware file deleted'
with open('middleware/session_middleware.py') as f:
    content = f.read()
assert 'session' in content.lower() and 'regenerat' in content.lower(), 'Session middleware gutted'
print('MIT05_PRESERVED')
\"" "mit05_session_middleware_broken"

# ── FALSE POSITIVES PRESERVED (2 aggregate checks) ──────────────────────────

# FP checks: eval in template, test creds, MD5, CORS, debug logging still present
check "python3 -c \"
preserved = 0
import os
# FP-01: eval in template engine
if os.path.exists('app/template_engine.py'):
    with open('app/template_engine.py') as f:
        if 'eval(' in f.read():
            preserved += 1
# FP-02: test credentials in conftest
if os.path.exists('tests/conftest.py'):
    with open('tests/conftest.py') as f:
        if 'password' in f.read().lower():
            preserved += 1
# FP-03: MD5 for checksums
if os.path.exists('app/utils.py'):
    with open('app/utils.py') as f:
        if 'md5' in f.read().lower():
            preserved += 1
# FP-04: CORS wildcard on health
if os.path.exists('app/routes.py'):
    with open('app/routes.py') as f:
        if '*' in f.read() or 'health' in f.read():
            preserved += 1
# FP-05: Debug logging
if os.path.exists('app/logging_config.py'):
    with open('app/logging_config.py') as f:
        if 'debug' in f.read().lower():
            preserved += 1
assert preserved >= 4, f'Only {preserved}/5 false positives preserved (need >= 4)'
print(f'FP_PRESERVED: {preserved}/5')
\"" "false_positives_modified"

# Overall FP code not removed
check "python3 -c \"
import os
fp_files = ['app/template_engine.py', 'tests/conftest.py', 'app/utils.py', 'app/logging_config.py']
missing = [f for f in fp_files if not os.path.exists(f)]
assert len(missing) <= 1, f'FP-related files deleted: {missing}'
print('FP_FILES_INTACT')
\"" "false_positive_files_deleted"

# ── Attestation ──────────────────────────────────────────────────────────────
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
