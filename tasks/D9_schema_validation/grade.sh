#!/usr/bin/env bash
# Grader for D9: JSON Schema Validation Pipeline
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

# 1. pipeline.py runs without error
check "python3 pipeline.py" "pipeline_crash"

# 2. Valid output exists
check "test -f data/output/valid.json" "missing_valid_output"

# 3. Invalid output exists
check "test -f data/output/invalid.json" "missing_invalid_output"

if [ -f data/output/valid.json ] && [ -f data/output/invalid.json ] && [ -f "$EXPECTED" ]; then

# 4. Correct valid count
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('data/output/valid.json') as f:
    valid = json.load(f)
assert len(valid) == expected['valid_count'], f'Expected {expected[\"valid_count\"]} valid, got {len(valid)}'
\"" "wrong_valid_count"

# 5. Correct invalid count
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('data/output/invalid.json') as f:
    invalid = json.load(f)
assert len(invalid) == expected['invalid_count'], f'Expected {expected[\"invalid_count\"]} invalid, got {len(invalid)}'
\"" "wrong_invalid_count"

# 6. Missing email records rejected
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('data/output/invalid.json') as f:
    invalid = json.load(f)
invalid_ids = [r.get('id', r.get('record', {}).get('id')) for r in invalid]
for rid in expected['missing_email_ids']:
    assert rid in invalid_ids, f'Record {rid} (missing email) not rejected'
\"" "missing_email_accepted"

# 7. Timestamps are integers in valid output
check "python3 -c \"
import json
with open('data/output/valid.json') as f:
    valid = json.load(f)
for r in valid:
    ts = r.get('created_at')
    assert isinstance(ts, int), f'Timestamp is {type(ts).__name__}, expected int: {ts}'
\"" "timestamp_not_int"

# 8. Booleans properly coerced
check "python3 -c \"
import json
expected = json.load(open('$EXPECTED'))
with open('data/output/valid.json') as f:
    valid = json.load(f)
for r in valid:
    v = r.get('verified')
    if v is not None:
        assert isinstance(v, bool), f'verified is {type(v).__name__}, expected bool: {v}'
\"" "boolean_not_coerced"

# 9. Status normalized to lowercase
check "python3 -c \"
import json
with open('data/output/valid.json') as f:
    valid = json.load(f)
for r in valid:
    s = r.get('status', '')
    assert s == s.lower(), f'Status not lowercase: {s}'
    assert s in ['active', 'inactive', 'pending'], f'Invalid status: {s}'
\"" "status_not_normalized"

fi

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
