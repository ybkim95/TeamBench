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

# 1. Pipeline runs without crashing
check "python3 pipeline.py" "pipeline_crash"

# 2. Output file exists with 18 records
check "python3 -c \"
import json
with open('data/processed.json') as f:
    records = json.load(f)
assert len(records) == 18, f'Expected 18 records, got {len(records)}'
print('RECORD_COUNT_OK')
\"" "wrong_record_count"

# 3. errors.jsonl exists with 2 entries
check "python3 -c \"
import json
with open('data/errors.jsonl') as f:
    errors = [json.loads(l) for l in f if l.strip()]
assert len(errors) == 2, f'Expected 2 errors, got {len(errors)}'
print('ERRORS_OK')
\"" "wrong_error_count"

# 4. No records silently dropped (18 valid + 2 errors = 20 input)
check "python3 -c \"
import json
with open('data/processed.json') as f:
    records = json.load(f)
with open('data/errors.jsonl') as f:
    errors = [json.loads(l) for l in f if l.strip()]
assert len(records) + len(errors) == 20, f'Records ({len(records)}) + errors ({len(errors)}) != 20'
print('NO_DROPPED_RECORDS')
\"" "records_silently_dropped"

# 5. Email validation accepts user+tag@example.com
check "python3 -c \"
import json
with open('data/processed.json') as f:
    records = json.load(f)
emails = [r['email'] for r in records]
assert 'charlie+work@example.com' in emails, 'Email with + rejected: charlie+work'
assert 'grace+dev@example.com' in emails, 'Email with + rejected: grace+dev'
assert 'mia+test@example.com' in emails, 'Email with + rejected: mia+test'
print('PLUS_EMAILS_OK')
\"" "plus_emails_rejected"

# 6. Report uses correct field names (name, not full_name)
check "python3 -c \"
import json
with open('data/processed.json') as f:
    records = json.load(f)
for r in records:
    assert 'name' in r, f'Missing name field: {r}'
    assert 'full_name' not in r, f'Should use name not full_name: {r}'
print('FIELD_NAMES_OK')
\"" "wrong_field_names"

# 7. Collector output is JSON array (not NDJSON)
check "python3 -c \"
import json
with open('data/collected.json') as f:
    data = json.load(f)
assert isinstance(data, list), f'Collector output is not a JSON array: {type(data)}'
print('JSON_ARRAY_OK')
\"" "collector_not_json_array"

# 8. Each record has required fields
check "python3 -c \"
import json
with open('data/processed.json') as f:
    records = json.load(f)
for r in records:
    for field in ['name', 'email', 'score', 'processed_at']:
        assert field in r, f'Missing field {field} in record: {r}'
print('FIELDS_OK')
\"" "missing_required_fields"

# 9. Integration test passes
check "python3 -m pytest tests/test_pipeline.py -q --tb=short 2>&1 | grep -q 'passed'" "integration_test_fail"

# 10. Report exists and mentions records
check "python3 -c \"
with open('data/report.txt') as f:
    report = f.read()
assert 'Alice' in report, 'Report missing records'
assert 'REPORT' in report, 'Report missing header'
print('REPORT_OK')
\"" "report_broken"

# 11. Diff is reasonable
check "python3 -c \"
import os
total = 0
for root, dirs, files in os.walk('.'):
    if '.git' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            total += os.path.getsize(os.path.join(root, f))
assert total < 10000, f'Total Python code too large: {total}'
print('DIFF_OK')
\"" "excessive_changes"

# 12. Attestation
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
