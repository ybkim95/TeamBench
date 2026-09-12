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

# ── Load seed-specific expected values ──────────────────────────────────────
EXPECTED_JSON="$REPORTS/expected.json"

APP_TYPE=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('app_type','api_server'))")
MODULE_NAME=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('module_name','app'))")
ERROR_CODES=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(json.dumps(d.get('error_codes',[])))")
HTTP_STATUSES=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(json.dumps(d.get('http_statuses',{})))")
RETRY_ATTEMPTS=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(d.get('retry_attempts',3))")
HAS_RETRY_AFTER=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(str(d.get('has_retry_after_header',True)).lower())")
HAS_SESSION_CLEAR=$(python3 -c "import json; d=json.load(open('$EXPECTED_JSON')); print(str(d.get('has_session_clear',True)).lower())")

cd "$WORKSPACE"

# ── CHECK 1: No bare except clauses in main module ───────────────────────────
check "python3 -c \"
import ast, sys
src = open('$MODULE_NAME.py').read()
tree = ast.parse(src)
bare = [n.lineno for n in ast.walk(tree)
        if isinstance(n, ast.ExceptHandler) and n.type is None]
assert not bare, f'Bare except clauses at lines: {bare}'
print('NO_BARE_EXCEPT_OK')
\"" "bare_except_clauses_present"

# ── CHECK 2: errors.py is importable and defines AppError ───────────────────
check "python3 -c \"
import sys
sys.path.insert(0, '.')
import errors
assert hasattr(errors, 'AppError'), 'AppError not defined in errors.py'
print('ERRORS_MODULE_OK')
\"" "errors_module_broken"

# ── CHECK 3: All required error code classes exist ───────────────────────────
check "python3 -c \"
import sys, json, inspect
sys.path.insert(0, '.')
import errors
codes = json.loads('$ERROR_CODES')
all_classes = {
    getattr(cls, 'code', None): cls
    for name, cls in inspect.getmembers(errors, inspect.isclass)
    if issubclass(cls, errors.AppError) and cls is not errors.AppError
}
missing = [c for c in codes if c not in all_classes]
assert not missing, f'Missing error classes for codes: {missing}'
print('ALL_ERROR_CLASSES_OK')
\"" "missing_error_classes"

# ── CHECK 4: HTTP statuses match spec ────────────────────────────────────────
check "python3 -c \"
import sys, json, inspect
sys.path.insert(0, '.')
import errors
statuses = json.loads(r'$HTTP_STATUSES')
all_classes = {
    getattr(cls, 'code', None): cls
    for name, cls in inspect.getmembers(errors, inspect.isclass)
    if issubclass(cls, errors.AppError) and cls is not errors.AppError
}
wrong = []
for code, expected_status in statuses.items():
    cls = all_classes.get(code)
    if cls and cls.http_status != expected_status:
        wrong.append(f'{code}: expected {expected_status}, got {cls.http_status}')
assert not wrong, f'Wrong HTTP statuses: {wrong}'
print('HTTP_STATUSES_OK')
\"" "wrong_http_statuses"

# ── CHECK 5: E001 InvalidInput returns 400 ───────────────────────────────────
check "python3 -c \"
import sys, json
sys.path.insert(0, '.')
from $MODULE_NAME import app
app.config['TESTING'] = True
client = app.test_client()
# Trigger invalid input: POST with empty body
with app.test_client() as c:
    resp = c.post(
        '/' + ('process' if '$APP_TYPE' in ('file_processor',) else
               'import/${MODULE_NAME}s' if '$APP_TYPE' == 'data_importer' else
               'webhook/${MODULE_NAME}s' if '$APP_TYPE' == 'webhook_handler' else
               '${MODULE_NAME}s'),
        json={},
        headers={'Authorization': 'Bearer valid-token'}
    )
    assert resp.status_code == 400, f'E001 InvalidInput: expected 400, got {resp.status_code}'
    data = json.loads(resp.data)
    assert 'error_code' in data, 'Response missing error_code field'
print('E001_STATUS_OK')
\"" "e001_wrong_status"

# ── CHECK 6: E002 NotFound returns 404 ───────────────────────────────────────
check "python3 -c \"
import sys, json
sys.path.insert(0, '.')
from $MODULE_NAME import app
app.config['TESTING'] = True
with app.test_client() as c:
    if '$APP_TYPE' == 'file_processor':
        resp = c.get('/status/__nonexistent__', headers={'Authorization': 'Bearer valid-token'})
    elif '$APP_TYPE' == 'data_importer':
        resp = c.get('/import/__nonexistent__s/__nonexistent__', headers={'Authorization': 'Bearer valid-token'})
    elif '$APP_TYPE' == 'webhook_handler':
        resp = c.get('/webhook/__nonexistent__s/__nonexistent__', headers={'Authorization': 'Bearer valid-token'})
    else:
        resp = c.get('/__nonexistent__s/__nonexistent__', headers={'Authorization': 'Bearer valid-token'})
    assert resp.status_code == 404, f'E002 NotFound: expected 404, got {resp.status_code}'
    data = json.loads(resp.data)
    assert 'error_code' in data, 'Response missing error_code field'
print('E002_STATUS_OK')
\"" "e002_wrong_status"

# ── CHECK 7: E003 RateLimit returns 429 + Retry-After ────────────────────────
check "python3 -c \"
import sys, json, time
sys.path.insert(0, '.')
import importlib
mod = importlib.import_module('$MODULE_NAME')
mod._REQUEST_COUNTS['grade_rl_test'] = [time.time()] * (mod._RATE_LIMIT + 1)
from $MODULE_NAME import app
app.config['TESTING'] = True
with app.test_client() as c:
    if '$APP_TYPE' == 'file_processor':
        resp = c.post('/validate', json={'file_type': 'pdf'},
                      headers={'Authorization': 'Bearer valid-token', 'X-Forwarded-For': 'grade_rl_test'})
    elif '$APP_TYPE' == 'data_importer':
        resp = c.post('/import/__nonexistent__s', json={'rows': []},
                      headers={'Authorization': 'Bearer valid-token', 'X-Forwarded-For': 'grade_rl_test'})
    elif '$APP_TYPE' == 'webhook_handler':
        resp = c.post('/webhook/__nonexistent__s',
                      json={'__nonexistent___type': 'test', 'event_id': 'rl_grade'},
                      headers={'Authorization': 'Bearer valid-token', 'X-Forwarded-For': 'grade_rl_test'})
    else:
        resp = c.get('/__nonexistent__s/x',
                     headers={'Authorization': 'Bearer valid-token', 'X-Forwarded-For': 'grade_rl_test'})
    assert resp.status_code == 429, f'E003 RateLimit: expected 429, got {resp.status_code}'
    assert 'Retry-After' in resp.headers, 'E003 RateLimit response missing Retry-After header'
print('E003_STATUS_AND_HEADER_OK')
\"" "e003_wrong_status_or_missing_header"

# ── CHECK 8: E005 AuthError returns 401 ──────────────────────────────────────
check "python3 -c \"
import sys, json
sys.path.insert(0, '.')
from $MODULE_NAME import app
app.config['TESTING'] = True
with app.test_client() as c:
    if '$APP_TYPE' == 'file_processor':
        resp = c.post('/validate', json={'file_type': 'pdf'}, headers={'Authorization': 'Bearer invalid'})
    elif '$APP_TYPE' == 'data_importer':
        resp = c.post('/import/__nonexistent__s', json={'rows': []}, headers={'Authorization': 'Bearer invalid'})
    elif '$APP_TYPE' == 'webhook_handler':
        resp = c.get('/webhook/__nonexistent__s/x', headers={'Authorization': 'Bearer invalid'})
    else:
        resp = c.get('/__nonexistent__s/x', headers={'Authorization': 'Bearer invalid'})
    assert resp.status_code == 401, f'E005 AuthError: expected 401, got {resp.status_code}'
    data = json.loads(resp.data)
    assert 'error_code' in data, 'Response missing error_code field'
print('E005_STATUS_OK')
\"" "e005_wrong_status"

# ── CHECK 9: E005 AuthError clears session ───────────────────────────────────
check "python3 -c \"
import sys, json
sys.path.insert(0, '.')
from $MODULE_NAME import app
app.config['TESTING'] = True
app.config['SECRET_KEY'] = 'test-secret'
with app.test_client() as c:
    with c.session_transaction() as sess:
        sess['user_id'] = 'test_user'
        sess['token'] = 'some_token'
    if '$APP_TYPE' == 'file_processor':
        resp = c.post('/validate', json={'file_type': 'pdf'}, headers={'Authorization': 'Bearer invalid'})
    elif '$APP_TYPE' == 'data_importer':
        resp = c.post('/import/__nonexistent__s', json={'rows': []}, headers={'Authorization': 'Bearer invalid'})
    elif '$APP_TYPE' == 'webhook_handler':
        resp = c.get('/webhook/__nonexistent__s/x', headers={'Authorization': 'Bearer invalid'})
    else:
        resp = c.get('/__nonexistent__s/x', headers={'Authorization': 'Bearer invalid'})
    assert resp.status_code == 401
    with c.session_transaction() as sess:
        assert 'user_id' not in sess, 'E005 AuthError must clear user_id from session'
print('E005_SESSION_CLEAR_OK')
\"" "e005_session_not_cleared"

# ── CHECK 10: E004 DatabaseError returns 503 after retries ───────────────────
check "python3 -c \"
import sys, json
sys.path.insert(0, '.')
from $MODULE_NAME import app
app.config['TESTING'] = True
with app.test_client() as c:
    if '$APP_TYPE' == 'file_processor':
        resp = c.get('/status/_fail_trigger', headers={'Authorization': 'Bearer valid-token'})
    elif '$APP_TYPE' == 'data_importer':
        resp = c.get('/import/__nonexistent__s/_fail_trigger', headers={'Authorization': 'Bearer valid-token'})
    elif '$APP_TYPE' == 'webhook_handler':
        resp = c.get('/webhook/__nonexistent__s/_fail_trigger', headers={'Authorization': 'Bearer valid-token'})
    else:
        resp = c.get('/__nonexistent__s/_fail_trigger', headers={'Authorization': 'Bearer valid-token'})
    assert resp.status_code == 503, f'E004 DatabaseError: expected 503, got {resp.status_code}'
    data = json.loads(resp.data)
    assert 'error_code' in data, 'Response missing error_code field'
print('E004_STATUS_OK')
\"" "e004_wrong_status"

# ── CHECK 11: Retry logic present in main module ──────────────────────────────
check "python3 -c \"
src = open('$MODULE_NAME.py').read()
has_retry = (
    'retry' in src.lower()
    or 'attempt' in src.lower()
    or 'for _ in range' in src
    or 'while' in src
)
assert has_retry, 'No retry logic found in $MODULE_NAME.py'
print('RETRY_LOGIC_PRESENT_OK')
\"" "retry_logic_missing"

# ── CHECK 12: All pytest tests pass ──────────────────────────────────────────
check "python3 -m pytest tests/test_error_handling.py -q --tb=no -p no:cacheprovider 2>&1 | tail -2 | grep -E '^[0-9]+ passed'" "tests_fail"

# ── CHECK 13: Zero test failures ─────────────────────────────────────────────
check "python3 -m pytest tests/test_error_handling.py -q --tb=no -p no:cacheprovider 2>&1 | grep -v 'warning' | grep -qv 'failed'" "tests_have_failures"

# ── CHECK 14: error_code field in all error responses ────────────────────────
check "python3 -c \"
import sys, json
sys.path.insert(0, '.')
from $MODULE_NAME import app
app.config['TESTING'] = True
with app.test_client() as c:
    # 404
    if '$APP_TYPE' == 'file_processor':
        resp = c.get('/status/__xyz__', headers={'Authorization': 'Bearer valid-token'})
    elif '$APP_TYPE' == 'data_importer':
        resp = c.get('/import/__nonexistent__s/__xyz__', headers={'Authorization': 'Bearer valid-token'})
    elif '$APP_TYPE' == 'webhook_handler':
        resp = c.get('/webhook/__nonexistent__s/__xyz__', headers={'Authorization': 'Bearer valid-token'})
    else:
        resp = c.get('/__nonexistent__s/__xyz__', headers={'Authorization': 'Bearer valid-token'})
    assert resp.status_code == 404
    data = json.loads(resp.data)
    assert 'error_code' in data, f'404 response missing error_code: {data}'
    assert data['error_code'] == 'E002', f'Expected E002, got {data[\"error_code\"]}'
print('ERROR_CODE_FIELD_OK')
\"" "error_code_field_missing"

# ── CHECK 15: Attestation ─────────────────────────────────────────────────────
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

# ── Score ─────────────────────────────────────────────────────────────────────
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
