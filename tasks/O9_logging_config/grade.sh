#!/usr/bin/env bash
# Grader for O9: Logging Configuration Fix
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

# 1. logging_config.py exists
check "test -f logging_config.py" "missing_logging_config"

# 2. app.py exists
check "test -f app.py" "missing_app"

# 3. Root log level is INFO
check "python3 -c \"
with open('logging_config.py') as f:
    content = f.read()
assert 'INFO' in content, 'Root log level not set to INFO'
# Check it is not DEBUG for root
import ast
tree = ast.parse(content)
# Simple heuristic: INFO appears in a level assignment context
assert content.count('DEBUG') == 0 or 'auth' in content.split('DEBUG')[0].split('\\n')[-1].lower(), 'Root still at DEBUG'
\"" "root_level_wrong"

# 4. Auth module at WARNING
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('logging_config.py') as f:
    content = f.read()
assert expected['auth_module'] in content, f'Auth module {expected[\"auth_module\"]} not configured'
assert 'WARNING' in content, 'WARNING level not found'
\"" "auth_level_wrong"

# 5. Structured JSON logging fields
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('logging_config.py') as f:
    content = f.read()
for field in expected['required_fields']:
    assert field in content, f'Missing structured field: {field}'
\"" "missing_structured_fields"

# 6. ISO-8601 timestamp format
check "python3 -c \"
with open('logging_config.py') as f:
    content = f.read()
assert '%Y-%m-%dT%H:%M:%S' in content or 'isoformat' in content or 'ISO' in content, 'No ISO-8601 timestamp format'
\"" "wrong_timestamp_format"

# 7. Rotation config correct
check "python3 -c \"
with open('logging_config.py') as f:
    content = f.read()
assert '10485760' in content or '10*1024*1024' in content or '10_485_760' in content, 'maxBytes not 10MB'
assert 'backupCount' in content or 'backup_count' in content, 'No backupCount set'
\"" "rotation_broken"

# 8. No PII in logs (email masked)
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('app.py') as f:
    content = f.read()
# Should not have raw email in log
assert 'f\"Processing user {email}\"' not in content and 'f\"Processing user {' not in content.replace('mask', 'FOUND'), 'Raw email still logged'
# Check for masking pattern
assert 'mask' in content.lower() or '***' in content or '[REDACTED]' in content or content.count('@') == 0 or 'email[0]' in content or 'email[:1]' in content, 'No email masking found'
\"" "pii_email_leaked"

# 9. No password hash in logs
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('app.py') as f:
    content = f.read()
# The password/hash logging line should be removed
assert expected['password_log_pattern'] not in content, 'Password hash still logged'
\"" "pii_password_leaked"

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
