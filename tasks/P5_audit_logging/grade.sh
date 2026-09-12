#!/usr/bin/env bash
# Seed-aware grader for P5: Audit Logging for Compliance
# Reads expected values from expected.json instead of hardcoded assertions.
#
# Args: $1=WORKSPACE $2=REPORTS $3=SUBMISSION $4=TASK_DIR [$5=EXPECTED_JSON]
set -o pipefail
WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"
EXPECTED="${5:-$REPORTS/expected.json}"

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

AUDIT_PY="$WORKSPACE/audit.py"
APP_PY="$WORKSPACE/app.py"

# ── Check 1: audit.py exists ──────────────────────────────────────────────────
check "test -f '$AUDIT_PY'" "missing_audit_py"

# ── Check 2: app.py exists ───────────────────────────────────────────────────
check "test -f '$APP_PY'" "missing_app_py"

# ── Check 3: audit.py is not just the stub (has real implementation) ──────────
check "python3 -c \"
import ast, sys
src = open('$AUDIT_PY').read()
tree = ast.parse(src)
has_impl = False
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name in ('log_event', 'get_log', 'verify_log'):
            body = node.body
            # Stub has only NotImplementedError or pass
            non_trivial = [n for n in body
                           if not isinstance(n, (ast.Pass, ast.Expr, ast.Raise))]
            if non_trivial:
                has_impl = True
assert has_impl, 'audit.py appears to be a stub with no implementation'
print('IMPL_OK')
\"" "audit_py_not_implemented"

if [ -f "$AUDIT_PY" ] && [ -f "$EXPECTED" ]; then

# ── Check 4: log_event() returns a dict with event_type ──────────────────────
check "python3 -c \"
import sys
sys.path.insert(0, '$WORKSPACE')
import json, importlib
expected = json.load(open('$EXPECTED'))
import audit
audit._AUDIT_LOG.clear()
ev_type = expected['required_event_types'][0]
req_fields = expected['required_fields_per_event'][ev_type]
universal = {'event_type', 'log_id', 'signature', 'prev_hash', 'checksum'}
payload = {f: f'test_{f}' for f in req_fields if f not in universal}
entry = audit.log_event(ev_type, **payload)
assert isinstance(entry, dict), 'log_event() must return a dict'
assert entry.get('event_type') == ev_type, f'event_type mismatch: {entry.get(\"event_type\")}'
print('LOG_EVENT_OK')
\"" "log_event_returns_wrong_type"

# ── Check 5: log_id is unique UUID-style string ───────────────────────────────
check "python3 -c \"
import sys
sys.path.insert(0, '$WORKSPACE')
import json
expected = json.load(open('$EXPECTED'))
import audit
audit._AUDIT_LOG.clear()
ev_type = expected['required_event_types'][0]
req_fields = expected['required_fields_per_event'][ev_type]
universal = {'event_type', 'log_id', 'signature', 'prev_hash', 'checksum'}
payload = {f: f'test_{f}' for f in req_fields if f not in universal}
e1 = audit.log_event(ev_type, **payload)
e2 = audit.log_event(ev_type, **payload)
assert 'log_id' in e1, 'missing log_id'
assert isinstance(e1['log_id'], str) and len(e1['log_id']) > 0, 'log_id must be non-empty string'
assert e1['log_id'] != e2['log_id'], 'log_id must be unique per entry'
print('LOG_ID_OK')
\"" "log_id_not_unique_or_missing"

# ── Check 6: get_log() returns list and accumulates entries ───────────────────
check "python3 -c \"
import sys
sys.path.insert(0, '$WORKSPACE')
import json
expected = json.load(open('$EXPECTED'))
import audit
audit._AUDIT_LOG.clear()
assert audit.get_log() == [], 'get_log() must return [] initially'
ev_type = expected['required_event_types'][0]
req_fields = expected['required_fields_per_event'][ev_type]
universal = {'event_type', 'log_id', 'signature', 'prev_hash', 'checksum'}
payload = {f: f'test_{f}' for f in req_fields if f not in universal}
audit.log_event(ev_type, **payload)
audit.log_event(ev_type, **payload)
log = audit.get_log()
assert isinstance(log, list), 'get_log() must return a list'
assert len(log) == 2, f'Expected 2 entries, got {len(log)}'
print('GET_LOG_OK')
\"" "get_log_wrong_behavior"

# ── Check 7: All required event types can be logged ──────────────────────────
check "python3 -c \"
import sys
sys.path.insert(0, '$WORKSPACE')
import json
expected = json.load(open('$EXPECTED'))
import audit
audit._AUDIT_LOG.clear()
universal = {'event_type', 'log_id', 'signature', 'prev_hash', 'checksum'}
for ev_type in expected['required_event_types']:
    req_fields = expected['required_fields_per_event'][ev_type]
    payload = {f: f'test_{f}' for f in req_fields if f not in universal}
    entry = audit.log_event(ev_type, **payload)
    assert isinstance(entry, dict), f'log_event({ev_type}) must return dict'
    assert entry.get('event_type') == ev_type, f'event_type field wrong for {ev_type}'
print('ALL_EVENT_TYPES_OK')
\"" "not_all_event_types_supported"

# ── Check 8: Required fields present per event type ───────────────────────────
check "python3 -c \"
import sys
sys.path.insert(0, '$WORKSPACE')
import json
expected = json.load(open('$EXPECTED'))
import audit
audit._AUDIT_LOG.clear()
universal = {'event_type', 'log_id', 'signature', 'prev_hash', 'checksum'}
for ev_type, req_fields in expected['required_fields_per_event'].items():
    payload = {f: f'test_{f}' for f in req_fields if f not in universal}
    entry = audit.log_event(ev_type, **payload)
    missing = [f for f in req_fields if f not in entry]
    assert not missing, f'Event {ev_type} entry missing fields: {missing}'
print('REQUIRED_FIELDS_OK')
\"" "required_fields_missing"

# ── Check 9: Tamper-detection field present on every entry ────────────────────
check "python3 -c \"
import sys
sys.path.insert(0, '$WORKSPACE')
import json
expected = json.load(open('$EXPECTED'))
import audit
audit._AUDIT_LOG.clear()
tamper_field = expected['tamper_detection_required_field']
universal = {'event_type', 'log_id', 'signature', 'prev_hash', 'checksum'}
for ev_type in expected['required_event_types']:
    req_fields = expected['required_fields_per_event'][ev_type]
    payload = {f: f'test_{f}' for f in req_fields if f not in universal}
    entry = audit.log_event(ev_type, **payload)
    assert tamper_field in entry, (
        f'Entry for {ev_type} missing tamper-detection field {tamper_field!r}'
    )
    assert entry[tamper_field], f'Tamper field {tamper_field!r} must not be empty'
print('TAMPER_FIELD_OK')
\"" "tamper_detection_field_missing"

# ── Check 10: verify_log() returns [] for untampered entries ─────────────────
check "python3 -c \"
import sys
sys.path.insert(0, '$WORKSPACE')
import json
expected = json.load(open('$EXPECTED'))
import audit
audit._AUDIT_LOG.clear()
universal = {'event_type', 'log_id', 'signature', 'prev_hash', 'checksum'}
for ev_type in expected['required_event_types']:
    req_fields = expected['required_fields_per_event'][ev_type]
    payload = {f: f'test_{f}' for f in req_fields if f not in universal}
    audit.log_event(ev_type, **payload)
entries = audit.get_log()
result = audit.verify_log(entries)
assert result == [], f'verify_log() must return [] for untampered log, got {result}'
print('VERIFY_LOG_CLEAN_OK')
\"" "verify_log_false_positive"

# ── Check 11: verify_log() detects a tampered entry ──────────────────────────
check "python3 -c \"
import sys
sys.path.insert(0, '$WORKSPACE')
import json
expected = json.load(open('$EXPECTED'))
import audit
audit._AUDIT_LOG.clear()
ev_type = expected['required_event_types'][0]
req_fields = expected['required_fields_per_event'][ev_type]
universal = {'event_type', 'log_id', 'signature', 'prev_hash', 'checksum'}
payload = {f: f'test_{f}' for f in req_fields if f not in universal}
audit.log_event(ev_type, **payload)
entries = audit.get_log()
tampered = [dict(e) for e in entries]
tamper_field = expected['tamper_detection_required_field']
# Remove tamper field to simulate tampering
tampered[0].pop(tamper_field, None)
tampered[0]['event_type'] = 'injected_event'
result = audit.verify_log(tampered)
assert 0 in result, f'verify_log() must detect tampered index 0, got {result}'
print('TAMPER_DETECTED_OK')
\"" "verify_log_tamper_not_detected"

# ── Check 12: app.py imports audit and calls log_event ───────────────────────
check "python3 -c \"
src = open('$APP_PY').read()
assert 'import audit' in src or 'from audit' in src, 'app.py must import audit'
assert 'log_event' in src, 'app.py must call audit.log_event()'
print('APP_INTEGRATION_OK')
\"" "app_py_missing_audit_integration"

# ── Check 13: verify_log() returns list type ──────────────────────────────────
check "python3 -c \"
import sys
sys.path.insert(0, '$WORKSPACE')
import audit
audit._AUDIT_LOG.clear()
result = audit.verify_log([])
assert isinstance(result, list), f'verify_log() must return a list, got {type(result)}'
print('VERIFY_RETURNS_LIST_OK')
\"" "verify_log_wrong_return_type"

fi

# ── Check 14: pytest test suite passes ───────────────────────────────────────
check "python3 -c \"
import subprocess, sys
result = subprocess.run(
    [sys.executable, '-m', 'pytest', '$WORKSPACE/tests/test_audit.py', '-q', '--tb=no'],
    capture_output=True, text=True, cwd='$WORKSPACE'
)
# Accept if at least 5 tests pass (partial credit)
lines = result.stdout
passed = 0
for line in lines.split('\n'):
    if 'passed' in line:
        import re
        m = re.search(r'(\d+) passed', line)
        if m:
            passed = int(m.group(1))
assert passed >= 5, f'pytest: only {passed} tests passed (need >= 5)'
print(f'PYTEST_{passed}_PASSED')
\"" "pytest_fewer_than_5_passed"

# ── Attestation check ─────────────────────────────────────────────────────────
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

# ── Write score.json ──────────────────────────────────────────────────────────
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
