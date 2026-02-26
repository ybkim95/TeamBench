#!/usr/bin/env bash
# Seed-aware grader for P3: RBAC Implementation
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

RBAC_PY="$WORKSPACE/rbac.py"
APP_PY="$WORKSPACE/app.py"

# ── Check 1: rbac.py exists and has valid Python syntax ──
check "python3 -m py_compile '$RBAC_PY' && echo OK" "rbac_py_syntax_error"

# ── Check 2: app.py exists and has valid Python syntax ──
check "python3 -m py_compile '$APP_PY' && echo OK" "app_py_syntax_error"

if [ -f "$RBAC_PY" ] && [ -f "$APP_PY" ] && [ -f "$EXPECTED" ]; then

# ── Check 3: PERMISSIONS dict is populated (not empty) ──
check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from rbac import PERMISSIONS
assert isinstance(PERMISSIONS, dict) and len(PERMISSIONS) > 0, \
    f'PERMISSIONS is empty or not a dict: {PERMISSIONS}'
print('PERMISSIONS_POPULATED')
\"" "permissions_dict_empty"

# ── Check 4: All required roles are present in PERMISSIONS ──
check "python3 -c \"
import sys, json; sys.path.insert(0, '$WORKSPACE')
from rbac import PERMISSIONS
expected = json.load(open('$EXPECTED'))
required_roles = set(expected['roles'])
actual_roles = set(PERMISSIONS.keys())
missing = required_roles - actual_roles
assert not missing, f'Missing roles in PERMISSIONS: {missing}'
print('ALL_ROLES_PRESENT')
\"" "missing_roles_in_permissions"

# ── Check 5: check_permission returns correct ALLOW decisions ──
check "python3 -c \"
import sys, json; sys.path.insert(0, '$WORKSPACE')
from rbac import check_permission
expected = json.load(open('$EXPECTED'))
allowed_checks = [p for p in expected['permissions'] if p['allowed']]
failures = []
for p in allowed_checks:
    result = check_permission(p['role'], p['endpoint'], p['method'])
    if not result:
        failures.append(f\"{p['role']} {p['method']} /{p['endpoint']} should be ALLOW\")
assert not failures, 'ALLOW failures: ' + '; '.join(failures[:5])
print('ALLOW_DECISIONS_CORRECT')
\"" "allow_decisions_wrong"

# ── Check 6: check_permission returns correct DENY decisions ──
check "python3 -c \"
import sys, json; sys.path.insert(0, '$WORKSPACE')
from rbac import check_permission
expected = json.load(open('$EXPECTED'))
denied_checks = [p for p in expected['permissions'] if not p['allowed']]
failures = []
for p in denied_checks:
    result = check_permission(p['role'], p['endpoint'], p['method'])
    if result:
        failures.append(f\"{p['role']} {p['method']} /{p['endpoint']} should be DENY\")
assert not failures, 'DENY failures: ' + '; '.join(failures[:5])
print('DENY_DECISIONS_CORRECT')
\"" "deny_decisions_wrong"

# ── Check 7: Flask app enforces ALLOW — allowed requests return 200 ──
check "python3 -c \"
import sys, json; sys.path.insert(0, '$WORKSPACE')
sys.path.insert(0, '$WORKSPACE')
import importlib, types

# Patch rbac before importing app
import rbac as rbac_mod
import app as app_mod

client = app_mod.app.test_client()
expected = json.load(open('$EXPECTED'))

allowed = [p for p in expected['permissions'] if p['allowed']]
failures = []
for p in allowed[:20]:  # check up to 20 allowed pairs
    resp = client.open(
        f\"/{p['endpoint']}\",
        method=p['method'],
        headers={'X-Role': p['role']},
    )
    if resp.status_code == 403:
        failures.append(f\"{p['role']} {p['method']} /{p['endpoint']} got 403, want 200\")
assert not failures, 'Flask ALLOW failures: ' + '; '.join(failures[:5])
print('FLASK_ALLOW_200_OK')
\"" "flask_allowed_returns_403"

# ── Check 8: Flask app enforces DENY — denied requests return 403 ──
check "python3 -c \"
import sys, json; sys.path.insert(0, '$WORKSPACE')

import rbac as rbac_mod
import app as app_mod

client = app_mod.app.test_client()
expected = json.load(open('$EXPECTED'))

denied = [p for p in expected['permissions'] if not p['allowed']]
failures = []
for p in denied[:20]:  # check up to 20 denied pairs
    resp = client.open(
        f\"/{p['endpoint']}\",
        method=p['method'],
        headers={'X-Role': p['role']},
    )
    if resp.status_code != 403:
        failures.append(f\"{p['role']} {p['method']} /{p['endpoint']} got {resp.status_code}, want 403\")
assert not failures, 'Flask DENY failures: ' + '; '.join(failures[:5])
print('FLASK_DENY_403_OK')
\"" "flask_denied_returns_200"

# ── Check 9: Audit trail is populated after requests ──
check "python3 -c \"
import sys, json; sys.path.insert(0, '$WORKSPACE')

import rbac as rbac_mod
import app as app_mod

client = app_mod.app.test_client()
expected = json.load(open('$EXPECTED'))

# Make a few requests to populate audit_trail
perms = expected['permissions'][:3]
for p in perms:
    client.open(f\"/{p['endpoint']}\", method=p['method'], headers={'X-Role': p['role']})

trail = app_mod.audit_trail
assert len(trail) >= len(perms), f'audit_trail has {len(trail)} entries, expected >= {len(perms)}'
# Check each entry has required fields
for entry in trail:
    assert 'role' in entry, f'audit entry missing role: {entry}'
    assert 'endpoint' in entry, f'audit entry missing endpoint: {entry}'
    assert 'method' in entry, f'audit entry missing method: {entry}'
    assert 'allowed' in entry, f'audit entry missing allowed: {entry}'
print('AUDIT_TRAIL_OK')
\"" "audit_trail_missing_or_incomplete"

# ── Check 10: No hardcoded bypass — unknown role is denied everywhere ──
check "python3 -c \"
import sys, json; sys.path.insert(0, '$WORKSPACE')
from rbac import check_permission
expected = json.load(open('$EXPECTED'))

# An unknown role should never be allowed
unknown_role = '__unknown_role_xyz__'
bypasses = []
for p in expected['permissions']:
    result = check_permission(unknown_role, p['endpoint'], p['method'])
    if result:
        bypasses.append(f\"{unknown_role} {p['method']} /{p['endpoint']} should be DENY\")
assert not bypasses, 'Hardcoded bypass detected: ' + '; '.join(bypasses[:5])
print('NO_HARDCODED_BYPASS')
\"" "hardcoded_bypass_detected"

fi

# ── Attestation ──
check "python3 -c \"
import json, sys
att_path = '$SUBMISSION/attestation.json'
try:
    att = json.load(open(att_path))
    assert att.get('verdict') == 'pass', f'verdict={att.get(\"verdict\")}'
except FileNotFoundError:
    raise AssertionError('attestation.json not found')
\" " "bad_attestation"

# Write score with partial scoring
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
