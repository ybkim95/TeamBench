#!/usr/bin/env bash
# Grader for P7: Data Retention Policy Compliance
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

cd "$WORKSPACE"
source /usr/local/lib/venv/bin/activate 2>/dev/null || true

# 1. manage.py exists
check "test -f manage.py" "missing_manage"

# 2. enforce runs without error
check "python3 manage.py enforce" "enforce_crash"

# 3. Expired records deleted
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('data/users.json') as f:
    users = json.load(f)
user_ids = [u['id'] for u in users]
for expired_id in expected['expired_ids']:
    assert expired_id not in user_ids, f'Expired user {expired_id} not deleted'
\"" "expired_not_deleted"

# 4. Non-expired records kept
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('data/users.json') as f:
    users = json.load(f)
user_ids = [u['id'] for u in users]
for keep_id in expected['keep_ids']:
    assert keep_id in user_ids, f'Active user {keep_id} was incorrectly deleted'
\"" "active_user_deleted"

# 5. Anonymize works on all PII fields
check "python3 -c \"
import json, subprocess, sys
expected = json.load(open('$EXPECTED'))
anon_id = expected['anonymize_test_id']
subprocess.run([sys.executable, 'manage.py', 'anonymize', str(anon_id)], check=True, timeout=10)
with open('data/users.json') as f:
    users = json.load(f)
user = next((u for u in users if u['id'] == anon_id), None)
assert user is not None, f'User {anon_id} not found after anonymize'
for field in ['name', 'email', 'phone']:
    assert user[field] == '[REDACTED]', f'{field} not anonymized: {user[field]}'
\"" "anonymize_incomplete"

# 6. Audit log exists and has entries
check "python3 -c \"
import json
with open('audit_log.json') as f:
    log = json.load(f)
assert isinstance(log, list), 'audit_log.json is not a list'
assert len(log) > 0, 'audit_log.json is empty'
\"" "no_audit_log"

# 7. Audit log entries have required fields
check "python3 -c \"
import json
with open('audit_log.json') as f:
    log = json.load(f)
required = ['timestamp', 'action', 'user_id', 'reason']
for entry in log:
    for field in required:
        assert field in entry, f'Audit entry missing field: {field}'
\"" "audit_fields_missing"

# 8. Audit log records deletion and anonymization
check "python3 -c \"
import json
with open('audit_log.json') as f:
    log = json.load(f)
actions = [e['action'] for e in log]
assert any('delet' in a.lower() or 'remov' in a.lower() or 'enforce' in a.lower() or 'expir' in a.lower() for a in actions), 'No deletion action in audit log'
assert any('anonym' in a.lower() or 'redact' in a.lower() for a in actions), 'No anonymization action in audit log'
\"" "audit_missing_actions"

# Attestation
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
    PASS=true
else
    PASS=false
fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $([ "$PASS" = "true" ] && echo 1 || echo 0)},
  "secondary": {
    "checks_passed": $PASSED,
    "checks_total": $CHECKS,
    "partial_score": $PARTIAL
  },
  "failure_modes": $FM
}
JSON
