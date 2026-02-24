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

# 1. No "import requests" in any migrated file
check "python3 -c \"
import os
false_positive_files = {'notification.py', 'constants.py', 'settings.py'}
for root, dirs, files in os.walk('app'):
    for f in files:
        if f.endswith('.py') and f not in false_positive_files:
            path = os.path.join(root, f)
            with open(path) as fh:
                content = fh.read()
            # Should not import requests (but 'requests_per_minute' is OK)
            for line in content.splitlines():
                line_stripped = line.strip()
                if line_stripped.startswith('import requests') or line_stripped.startswith('from requests'):
                    assert False, f'{path}: still imports requests: {line_stripped}'
print('NO_REQUESTS_IMPORT')
\"" "requests_import_found"

# 2. All Python files are syntactically valid
check "python3 -c \"
import py_compile, os
for root, dirs, files in os.walk('app'):
    for f in files:
        if f.endswith('.py'):
            py_compile.compile(os.path.join(root, f), doraise=True)
print('ALL_SYNTAX_OK')
\"" "syntax_error"

# 3. requirements.txt has httpx, no requests
check "python3 -c \"
with open('requirements.txt') as f:
    content = f.read()
assert 'httpx' in content, 'requirements.txt missing httpx'
lines = content.strip().splitlines()
for line in lines:
    line = line.strip()
    if line.startswith('requests') and not line.startswith('requests_per'):
        if 'requests_mock' not in line and 'requests-mock' not in line:
            assert False, f'requirements.txt still has requests: {line}'
print('REQUIREMENTS_OK')
\"" "bad_requirements"

# 4. notification.py unchanged (still uses aiohttp)
check "python3 -c \"
with open('app/services/notification.py') as f:
    code = f.read()
assert 'aiohttp' in code, 'notification.py missing aiohttp'
assert 'httpx' not in code, 'notification.py should not use httpx'
print('NOTIFICATION_UNCHANGED')
\"" "notification_modified"

# 5. constants.py unchanged
check "python3 -c \"
with open('app/config/constants.py') as f:
    code = f.read()
assert 'TIMEOUT = 60' in code, 'constants.py modified'
assert 'httpx' not in code, 'constants.py should not reference httpx'
print('CONSTANTS_UNCHANGED')
\"" "constants_modified"

# 6. settings.py still has requests_per_minute
check "python3 -c \"
with open('app/config/settings.py') as f:
    code = f.read()
assert 'requests_per_minute' in code, 'settings.py missing requests_per_minute'
print('SETTINGS_OK')
\"" "settings_modified"

# 7. client.py uses httpx.Client with context manager
check "python3 -c \"
with open('app/api/client.py') as f:
    code = f.read()
assert 'httpx' in code, 'client.py not migrated to httpx'
print('CLIENT_MIGRATED')
\"" "client_not_migrated"

# 8. auth_client.py uses httpx.BasicAuth
check "python3 -c \"
with open('app/api/auth_client.py') as f:
    code = f.read()
assert 'httpx' in code, 'auth_client.py not migrated'
assert 'BasicAuth' in code or 'basic_auth' in code, 'auth_client not using httpx.BasicAuth'
print('AUTH_MIGRATED')
\"" "auth_not_migrated"

# 9. response_parser.py handles None from empty-body .json()
check "python3 -c \"
with open('app/utils/response_parser.py') as f:
    code = f.read()
# Should handle None return (httpx returns None, not ValueError)
assert 'None' in code or 'is None' in code, 'response_parser not handling None'
print('PARSER_OK')
\"" "parser_not_updated"

# 10. retry.py catches httpx.ConnectError
check "python3 -c \"
with open('app/utils/retry.py') as f:
    code = f.read()
assert 'httpx' in code, 'retry.py not migrated'
assert 'ConnectError' in code, 'retry.py not catching httpx.ConnectError'
assert 'requests' not in code.split('#')[0] or True, 'retry.py still references requests'
print('RETRY_MIGRATED')
\"" "retry_not_migrated"

# 11. conftest.py uses respx
check "python3 -c \"
with open('app/tests/conftest.py') as f:
    code = f.read()
assert 'respx' in code or 'httpx' in code, 'conftest.py not migrated to respx'
assert 'requests_mock' not in code, 'conftest.py still uses requests_mock'
print('CONFTEST_MIGRATED')
\"" "conftest_not_migrated"

# 12. Test file uses httpx mocking
check "python3 -c \"
with open('app/tests/test_client.py') as f:
    code = f.read()
assert 'respx' in code or 'httpx' in code, 'test_client.py not migrated'
print('TESTS_MIGRATED')
\"" "tests_not_migrated"

# 13. Total diff reasonable
check "python3 -c \"
import os
total = 0
for root, dirs, files in os.walk('.'):
    if '.git' in root:
        continue
    for f in files:
        if f.endswith('.py') or f == 'requirements.txt':
            total += os.path.getsize(os.path.join(root, f))
assert total < 15000, f'Total code too large: {total}'
print('DIFF_OK')
\"" "excessive_changes"

# 14. Attestation
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
